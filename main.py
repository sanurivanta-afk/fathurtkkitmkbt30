import os
import json
import asyncio
from datetime import datetime

import requests
import redis

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================
# ENV VARS
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
KNOWN_SET_KEY = "tokoku:known_ids"
LAST_STATUS_KEY = "tokoku:last_status"
LAST_HTTP_KEY = "tokoku:last_http"
LAST_CHECK_TS_KEY = "tokoku:last_check_ts"
COOKIE_EXPIRED_FLAG_KEY = "tokoku:cookie_expired_notified"

# =========================
# TOKOKU ENDPOINTS
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


# =========================
# HELPERS
# =========================
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
# TOKOKU LOGIC (BLOCKING)
# =========================
def fetch_orders():
    params = {
        "status": 2,
        "page": 1,
        "sort": "oldest",
        "use_simple_pagination": "true",
        "language_code": "ID",
    }
    try:
        r = session.get(BASE_URL_ORDER_HISTORY, params=params, timeout=15)
    except Exception:
        return -1, []

    if r.status_code != 200:
        return r.status_code, []

    try:
        data = r.json()["data"]["data"]
        return 200, data if isinstance(data, list) else []
    except Exception:
        return r.status_code, []


def extract_oid(o):
    return o.get("order_number") or o.get("id")


def extract_deliver_id(o):
    return o.get("order_id") or o.get("id")


def deliver_order(o):
    oid = extract_deliver_id(o)
    if not oid:
        return False, 0, "order_id not found"

    try:
        r = session.post(DELIVER_URL, json={"order_id": oid}, timeout=15)
    except Exception as e:
        return False, -1, str(e)

    if r.status_code != 200:
        return False, r.status_code, r.text[:150]

    return True, 200, "OK"


def prime_known(r, orders):
    if r.scard(KNOWN_SET_KEY) > 0:
        return False
    for o in orders:
        oid = extract_oid(o)
        if oid:
            r.sadd(KNOWN_SET_KEY, str(oid))
    return True


# =========================
# MONITOR (ASYNC)
# =========================
async def monitor_tick(context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    r = redis_client()

    cookie = get_cookie(r)
    apply_cookie(cookie)

    if not cookie:
        set_status(r, "NO_COOKIE", 0)
        if r.get(COOKIE_EXPIRED_FLAG_KEY) != "1":
            r.set(COOKIE_EXPIRED_FLAG_KEY, "1")
            await app.bot.send_message(ALLOWED_CHAT_ID, "Cookie belum diset.")
        return

    http, orders = await asyncio.to_thread(fetch_orders)
    set_status(r, "CHECK", http)

    if http in (401, 403):
        set_status(r, "COOKIE_EXPIRED", http)
        if r.get(COOKIE_EXPIRED_FLAG_KEY) != "1":
            r.set(COOKIE_EXPIRED_FLAG_KEY, "1")
            await app.bot.send_message(ALLOWED_CHAT_ID, "COOKIE EXPIRED")
        return

    if http != 200:
        return

    r.delete(COOKIE_EXPIRED_FLAG_KEY)

    if prime_known(r, orders):
        await app.bot.send_message(ALLOWED_CHAT_ID, f"Monitor aktif. Prime {len(orders)} order awal.")
        return

    baru = []
    for o in orders:
        oid = extract_oid(o)
        if not oid:
            continue
        if not r.sismember(KNOWN_SET_KEY, str(oid)):
            r.sadd(KNOWN_SET_KEY, str(oid))
            baru.append(o)

    if baru:
        ids = [str(extract_oid(o)) for o in baru]
        await app.bot.send_message(ALLOWED_CHAT_ID, f"Pesanan baru: {', '.join(ids)}")

        for o in baru:
            oid = extract_oid(o)
            ok, code, msg = await asyncio.to_thread(deliver_order, o)
            if ok:
                await app.bot.send_message(ALLOWED_CHAT_ID, f"DELIVER OK: {oid}")
            else:
                await app.bot.send_message(ALLOWED_CHAT_ID, f"DELIVER FAIL: {oid} ({code})")


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
        f"Last: {r.get(LAST_CHECK_TS_KEY)}\n"
        f"Status: {r.get(LAST_STATUS_KEY)}\n"
        f"HTTP: {r.get(LAST_HTTP_KEY)}"
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
