import os
import asyncio
from datetime import datetime

import requests
import redis

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# ENV
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
ALLOWED_CHAT_ID = int(os.environ["ALLOWED_CHAT_ID"])
BOT_PIN = os.environ["BOT_PIN"]

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
REDIS_SSL = os.environ.get("REDIS_SSL", "false").lower() in ("1", "true", "yes")

# =========================
# REDIS KEYS
# =========================
COOKIE_KEY = "tokoku:cookie"
DELIVERED_SET_KEY = "tokoku:delivered_ids"

LAST_STATUS_KEY = "tokoku:last_status"
LAST_HTTP_KEY = "tokoku:last_http"
LAST_CHECK_TS_KEY = "tokoku:last_check_ts"
COOKIE_EXPIRED_FLAG_KEY = "tokoku:cookie_expired_notified"

# =========================
# TOKOKU ENDPOINTS
# (sesuaikan kalau di script aslimu beda)
# =========================
BASE_URL_ORDER_HISTORY = "https://tokoku-gateway.itemku.com/order-history"
DELIVER_URL = "https://tokoku-gateway.itemku.com/order-history/deliver"

# =========================
# GLOBALS
# =========================
monitor_job = None

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "client-id": "seller-web_ccdec37602b77fa07608c7afdcfdc7e9",
    "Referer": "https://tokoku.itemku.com/riwayat-pesanan",
    "Origin": "https://tokoku.itemku.com",
})


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_allowed(update: Update) -> bool:
    return update.effective_chat and update.effective_chat.id == ALLOWED_CHAT_ID


def redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        username="default",
        ssl=REDIS_SSL,
        decode_responses=True,
    )


def get_cookie(r):
    return (r.get(COOKIE_KEY) or "").strip()


def set_cookie(r, cookie: str):
    r.set(COOKIE_KEY, cookie.strip())
    r.delete(COOKIE_EXPIRED_FLAG_KEY)


def apply_cookie(cookie: str):
    if cookie:
        session.headers["Cookie"] = cookie
    else:
        session.headers.pop("Cookie", None)


def set_status(r, status, http):
    r.set(LAST_STATUS_KEY, status)
    r.set(LAST_HTTP_KEY, str(http))
    r.set(LAST_CHECK_TS_KEY, now_str())


# =========================
# TOKOKU (blocking)
# =========================
def fetch_orders_status_2():
    """
    Ambil pesanan 'perlu diproses' (status=2).
    """
    params = {
        "status": 2,
        "page": 1,
        "sort": "oldest",
        "use_simple_pagination": "true",
        "language_code": "ID",
    }
    try:
        resp = session.get(BASE_URL_ORDER_HISTORY, params=params, timeout=15)
    except Exception:
        return -1, []

    if resp.status_code != 200:
        return resp.status_code, []

    try:
        data = resp.json().get("data", {}).get("data", [])
        return 200, data if isinstance(data, list) else []
    except Exception:
        return resp.status_code, []


def extract_order_number(o):
    # tampilkan id yang enak dibaca di notif
    return o.get("order_number") or o.get("id") or o.get("order_id")


def extract_deliver_id(o):
    # id yang dipakai endpoint deliver (sesuaikan kalau script aslimu beda)
    return o.get("order_id") or o.get("id")


def deliver_order(o):
    deliver_id = extract_deliver_id(o)
    if not deliver_id:
        return False, 0, "deliver_id not found"

    try:
        resp = session.post(DELIVER_URL, json={"order_id": deliver_id}, timeout=15)
    except Exception as e:
        return False, -1, str(e)

    if resp.status_code != 200:
        return False, resp.status_code, resp.text[:150]

    return True, 200, "OK"


# =========================
# MONITOR (async job)
# =========================
async def monitor_tick(context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    r = redis_client()

    cookie = get_cookie(r)
    apply_cookie(cookie)

    if not cookie:
        set_status(r, "NO_COOKIE", 0)
        return

    http, orders = await asyncio.to_thread(fetch_orders_status_2)
    set_status(r, "CHECK", http)

    # cookie expired
    if http in (401, 403):
        set_status(r, "COOKIE_EXPIRED", http)
        if r.get(COOKIE_EXPIRED_FLAG_KEY) != "1":
            r.set(COOKIE_EXPIRED_FLAG_KEY, "1")
            await app.bot.send_message(ALLOWED_CHAT_ID, "COOKIE EXPIRED. Kirim /setcookie PIN <cookie_baru>")
        return

    if http != 200:
        # error lain, diam saja (biar ga spam)
        return

    r.delete(COOKIE_EXPIRED_FLAG_KEY)

    if not orders:
        # tidak ada pesanan perlu diproses
        return

    # proses semua yang status=2
    for o in orders:
        oid_show = extract_order_number(o)
        deliver_id = extract_deliver_id(o)

        # anti-repeat: kalau sudah sukses deliver sebelumnya, skip
        if deliver_id and r.sismember(DELIVERED_SET_KEY, str(deliver_id)):
            continue

        ok, code, _ = await asyncio.to_thread(deliver_order, o)

        if ok:
            if deliver_id:
                r.sadd(DELIVERED_SET_KEY, str(deliver_id))
            await app.bot.send_message(ALLOWED_CHAT_ID, f"DELIVER OK: {oid_show}")
        else:
            await app.bot.send_message(ALLOWED_CHAT_ID, f"DELIVER FAIL: {oid_show} (HTTP {code})")


# =========================
# COMMANDS
# =========================
async def cmd_start_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global monitor_job
    if not is_allowed(update):
        return

    if monitor_job:
        await update.message.reply_text("Monitor sudah ON.")
        return

    monitor_job = context.job_queue.run_repeating(monitor_tick, interval=10, first=0)
    await update.message.reply_text("Monitor ON.")


async def cmd_stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global monitor_job
    if not is_allowed(update):
        return

    if monitor_job:
        monitor_job.schedule_removal()
        monitor_job = None

    await update.message.reply_text("Monitor OFF.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    r = redis_client()
    run = "ON" if monitor_job else "OFF"
    await update.message.reply_text(
        f"Run: {run}\n"
        f"Last: {r.get(LAST_CHECK_TS_KEY) or '-'}\n"
        f"Status: {r.get(LAST_STATUS_KEY) or 'UNKNOWN'}\n"
        f"HTTP: {r.get(LAST_HTTP_KEY) or '-'}"
    )


async def cmd_setcookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    parts = update.message.text.split(" ", 2)
    if len(parts) < 3:
        await update.message.reply_text("Format: /setcookie PIN COOKIE")
        return

    if parts[1] != BOT_PIN:
        await update.message.reply_text("PIN salah.")
        return

    r = redis_client()
    set_cookie(r, parts[2])
    await update.message.reply_text("Cookie updated.")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start_monitor", cmd_start_monitor))
    app.add_handler(CommandHandler("stop_monitor", cmd_stop_monitor))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("setcookie", cmd_setcookie))

    app.run_polling()


if __name__ == "__main__":
    main()
