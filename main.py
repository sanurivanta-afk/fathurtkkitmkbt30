import os
import time
import json
import threading
from datetime import datetime

import requests
import redis

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# ENV VARS (Render)
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
ALLOWED_CHAT_ID = int(os.environ["ALLOWED_CHAT_ID"])
BOT_PIN = os.environ["BOT_PIN"]

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
# Redis Cloud biasanya butuh TLS. Default true.
REDIS_SSL = os.environ.get("REDIS_SSL", "true").lower() in ("1", "true", "yes")

# =========================
# REDIS KEYS
# =========================
COOKIE_KEY = "tokoku:cookie"
KNOWN_SET_KEY = "tokoku:known_ids"
LAST_STATUS_KEY = "tokoku:last_status"
LAST_HTTP_KEY = "tokoku:last_http"
LAST_CHECK_TS_KEY = "tokoku:last_check_ts"
COOKIE_EXPIRED_FLAG_KEY = "tokoku:cookie_expired_notified"  # "1" jika sudah notif

# =========================
# TOKOKU ENDPOINTS (SAMA DENGAN SCRIPT KAMU)
# =========================
BASE_URL_ORDER_HISTORY = "https://tokoku-gateway.itemku.com/order-history"
DELIVER_URL = "https://tokoku-gateway.itemku.com/order-history/deliver"

# =========================
# GLOBAL STATE (RAM)
# =========================
running = False
monitor_thread = None

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "Accept": "application/json, text/plain, */*",
    "client-id": "seller-web_ccdec37602b77fa07608c7afdcfdc7e9",
    "Referer": "https://tokoku.itemku.com/riwayat-pesanan?tab=0&searchType=Nomor+Pesanan&sort=oldest",
    "Origin": "https://tokoku.itemku.com",
})


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_allowed(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.id == ALLOWED_CHAT_ID)


def redis_client() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        username="default",
        ssl=REDIS_SSL,
        decode_responses=True,
    )


def get_cookie(r: redis.Redis) -> str:
    val = r.get(COOKIE_KEY)
    return val.strip() if val else ""


def set_cookie(r: redis.Redis, cookie: str):
    r.set(COOKIE_KEY, cookie.strip())
    # reset flag notif expired supaya bisa notif lagi kalau expired di masa depan
    r.delete(COOKIE_EXPIRED_FLAG_KEY)


def apply_cookie_to_session(cookie: str):
    # Cookie diset ke header session
    if cookie:
        session.headers.update({"Cookie": cookie})
    else:
        # kalau kosong, hapus header Cookie agar jelas gagal
        if "Cookie" in session.headers:
            session.headers.pop("Cookie", None)


def get_pesanan_perlu_diproses() -> tuple[int, list]:
    """
    Return: (http_status, orders_list)
    """
    params = {
        "status": 2,  # 2 = Perlu Diproses
        "page": 1,
        "sort": "oldest",
        "include_order_seller": 1,
        "include_order_info": 1,
        "include_order_reroute_flow": 1,
        "include_order_booking": 1,
        "search_type": "order_number",
        "use_simple_pagination": "true",
        "language_code": "ID",
    }

    try:
        resp = session.get(BASE_URL_ORDER_HISTORY, params=params, timeout=(5, 20))
    except Exception:
        return -1, []

    if resp.status_code != 200:
        return resp.status_code, []

    try:
        payload = resp.json()
        orders = payload["data"]["data"]
        if not isinstance(orders, list):
            return resp.status_code, []
        return resp.status_code, orders
    except Exception:
        return resp.status_code, []


def extract_oid(order: dict):
    return order.get("order_number") or order.get("order_code") or order.get("id")


def extract_order_id_for_deliver(order: dict):
    # mengikuti script kamu
    return order.get("order_id") or order.get("id") or order.get("order_number")


def kirim_pesanan(order: dict) -> tuple[bool, int, str]:
    """
    Return: (success, http_code, msg_short)
    """
    order_id = extract_order_id_for_deliver(order)
    if not order_id:
        return False, 0, "order_id tidak ditemukan"

    payload = {"order_id": order_id}
    try:
        resp = session.post(DELIVER_URL, json=payload, timeout=(5, 20))
    except Exception as e:
        return False, -1, f"error: {str(e)[:120]}"

    if resp.status_code != 200:
        return False, resp.status_code, resp.text[:200]

    # kalau JSON ada message
    try:
        j = resp.json()
        return True, resp.status_code, json.dumps(j)[:200]
    except Exception:
        return True, resp.status_code, resp.text[:200]


async def tg_send(app: Application, text: str):
    await app.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=text)


def set_last_status(r: redis.Redis, status: str, http_code: int | str):
    r.set(LAST_STATUS_KEY, status)
    r.set(LAST_HTTP_KEY, str(http_code))
    r.set(LAST_CHECK_TS_KEY, now_str())


def prime_known_orders(r: redis.Redis, orders: list):
    """
    Kalau KNOWN_SET kosong (first run), kita isi dulu tanpa auto-deliver.
    Ini mencegah 'banjir auto deliver' saat pertama kali pindah ke cloud.
    """
    if r.scard(KNOWN_SET_KEY) != 0:
        return False
    for o in orders:
        oid = extract_oid(o)
        if oid:
            r.sadd(KNOWN_SET_KEY, str(oid))
    return True


def monitor_loop(app: Application, delay: int = 10):
    global running

    r = redis_client()

    while running:
        # ambil cookie dari redis & apply ke session
        cookie = get_cookie(r)
        apply_cookie_to_session(cookie)

        if not cookie:
            set_last_status(r, "NO_COOKIE", "0")
            # notif 1x (jangan spam)
            if r.get(COOKIE_EXPIRED_FLAG_KEY) != "1":
                r.set(COOKIE_EXPIRED_FLAG_KEY, "1")
                app.create_task(tg_send(app, "Cookie belum diset. Kirim /setcookie <PIN> <cookie_baru>"))
            time.sleep(15)
            continue

        http_code, orders = get_pesanan_perlu_diproses()
        set_last_status(r, "CHECK", http_code)

        # cookie expired / unauthorized
        if http_code in (401, 403):
            set_last_status(r, "COOKIE_EXPIRED", http_code)
            if r.get(COOKIE_EXPIRED_FLAG_KEY) != "1":
                r.set(COOKIE_EXPIRED_FLAG_KEY, "1")
                app.create_task(tg_send(app, f"COOKIE EXPIRED (HTTP {http_code}). Kirim /setcookie <PIN> <cookie_baru>"))
            time.sleep(20)
            continue

        # error lain
        if http_code != 200:
            # notif error tapi throttled (pakai flag yang sama supaya tidak spam)
            if r.get(COOKIE_EXPIRED_FLAG_KEY) != "1":
                r.set(COOKIE_EXPIRED_FLAG_KEY, "1")
                app.create_task(tg_send(app, f"ERROR cek pesanan (HTTP {http_code})."))
            time.sleep(15)
            continue
        else:
            # kalau sudah normal, reset flag supaya error berikutnya bisa notif lagi
            r.delete(COOKIE_EXPIRED_FLAG_KEY)

        # first run prime
        if prime_known_orders(r, orders):
            app.create_task(tg_send(app, f"Monitor aktif. Prime {len(orders)} order awal (tanpa auto-deliver)."))
            time.sleep(delay)
            continue

        # cari yang baru
        baru = []
        for o in orders:
            oid = extract_oid(o)
            if not oid:
                continue
            oid = str(oid)
            if not r.sismember(KNOWN_SET_KEY, oid):
                r.sadd(KNOWN_SET_KEY, oid)
                baru.append(o)

        if baru:
            # notif ringkas
            ids = []
            for o in baru[:10]:
                ids.append(str(extract_oid(o)))
            extra = "" if len(baru) <= 10 else f" (+{len(baru)-10} lainnya)"
            app.create_task(tg_send(app, f"Ada {len(baru)} pesanan baru: {', '.join(ids)}{extra}"))

            # auto deliver satu-satu
            for o in baru:
                oid = extract_oid(o)
                ok, code, msg = kirim_pesanan(o)
                if ok:
                    app.create_task(tg_send(app, f"DELIVER OK: {oid} (HTTP {code})"))
                else:
                    app.create_task(tg_send(app, f"DELIVER FAIL: {oid} (HTTP {code}) {msg}"))

        time.sleep(delay)


# =========================
# TELEGRAM COMMANDS
# =========================
async def cmd_start_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running, monitor_thread
    if not is_allowed(update):
        return

    if running:
        await update.message.reply_text("Monitor sudah ON.")
        return

    running = True
    monitor_thread = threading.Thread(
        target=monitor_loop,
        args=(context.application, 10),
        daemon=True
    )
    monitor_thread.start()
    await update.message.reply_text("Monitor ON.")


async def cmd_stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    if not is_allowed(update):
        return

    running = False
    await update.message.reply_text("Monitor OFF.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    r = redis_client()
    st = r.get(LAST_STATUS_KEY) or "UNKNOWN"
    http_code = r.get(LAST_HTTP_KEY) or "-"
    ts = r.get(LAST_CHECK_TS_KEY) or "-"
    run = "ON" if running else "OFF"
    await update.message.reply_text(
        f"Run: {run}\nLast: {ts}\nStatus: {st}\nHTTP: {http_code}"
    )


async def cmd_testcookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    r = redis_client()
    cookie = get_cookie(r)
    apply_cookie_to_session(cookie)
    if not cookie:
        await update.message.reply_text("Cookie belum diset.")
        return

    http_code, _ = get_pesanan_perlu_diproses()
    if http_code == 200:
        await update.message.reply_text("Cookie VALID (HTTP 200).")
    elif http_code in (401, 403):
        await update.message.reply_text(f"Cookie EXPIRED (HTTP {http_code}).")
    else:
        await update.message.reply_text(f"Cookie ERROR/UNKNOWN (HTTP {http_code}).")


async def cmd_setcookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Format: /setcookie <PIN> <cookie_baru>
    """
    if not is_allowed(update):
        return

    text = (update.message.text or "").strip()
    parts = text.split(" ", 2)
    if len(parts) < 3:
        await update.message.reply_text("Format: /setcookie <PIN> <cookie_baru>")
        return

    pin = parts[1].strip()
    cookie_new = parts[2].strip()

    if pin != BOT_PIN:
        await update.message.reply_text("PIN salah.")
        return

    r = redis_client()
    set_cookie(r, cookie_new)
    apply_cookie_to_session(cookie_new)

    # test langsung
    http_code, _ = get_pesanan_perlu_diproses()
    if http_code == 200:
        await update.message.reply_text("Cookie updated & VALID (HTTP 200).")
        # reset notif flag supaya normal
        r.delete(COOKIE_EXPIRED_FLAG_KEY)
    elif http_code in (401, 403):
        await update.message.reply_text(f"Cookie updated tapi masih EXPIRED (HTTP {http_code}).")
    else:
        await update.message.reply_text(f"Cookie updated tapi ERROR/UNKNOWN (HTTP {http_code}).")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start_monitor", cmd_start_monitor))
    app.add_handler(CommandHandler("stop_monitor", cmd_stop_monitor))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("testcookie", cmd_testcookie))
    app.add_handler(CommandHandler("setcookie", cmd_setcookie))

    app.run_polling()


if __name__ == "__main__":
    main()
