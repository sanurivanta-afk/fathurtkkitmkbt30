import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from fitur_gopay import cek_akun_gopay, get_katalog_gopay_text, eksekusi_order_gopay
import os

# Import fungsi dari file modular kita
from fitur_promo import cek_promo
from fitur_order import get_katalog_text, eksekusi_order

# Mengambil Token dari Environment Variable Render
TOKEN = os.environ.get("TOKEN_BOT_KASIR") 
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

@bot.message_handler(commands=['start', 'menu'])
def menu_utama(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🛒 Order via Mobapay", callback_data="menu_order_moba"),
        InlineKeyboardButton("🟢 Order via GoPay (Cek Region)", callback_data="menu_order_gopay"),
        InlineKeyboardButton("🎁 Cek Promo First Recharge", callback_data="menu_promo")
    )
    bot.send_message(message.chat.id, "🤖 *DASHBOARD KASIR*\nPilih menu di bawah ini:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def urus_tombol(call):
    chat_id = call.message.chat.id
    
    # 1. CEK PROMO
    if call.data == "menu_promo":
        msg = bot.send_message(chat_id, "🎁 *CEK PROMO*\nKirimkan ID dan Server\nContoh: `152701842,2764`")
        bot.register_next_step_handler(msg, proses_promo)
        
    # 2. ORDER MOBAPAY (Bug Diperbaiki Di Sini)
    elif call.data == "menu_order_moba": 
        msg = bot.send_message(chat_id, "🛒 *BUAT ORDER MOBAPAY*\nKirimkan ID dan Server Pembeli\nContoh: `152701842,2764`")
        bot.register_next_step_handler(msg, proses_order_step1)
        
    # 3. ORDER GOPAY
    elif call.data == "menu_order_gopay":
        msg = bot.send_message(chat_id, "🟢 *ORDER GOPAY*\nKirimkan ID dan Server Pembeli\nContoh: `152701842,2764`")
        bot.register_next_step_handler(msg, proses_gopay_step1)


# --- FUNGSI LANJUTAN (NEXT STEP HANDLERS) ---
def parse_id(text):
    try:
        uid, zid = text.split(",")
        return uid.strip(), zid.strip()
    except ValueError:
        return None, None

def proses_promo(message):
    uid, zid = parse_id(message.text)
    if not uid:
        bot.send_message(message.chat.id, "❌ Format salah! Harus pakai koma.")
        return
    bot.send_message(message.chat.id, "⏳ Sedang mengecek ke server Mobapay...")
    hasil = cek_promo(uid, zid)
    bot.send_message(message.chat.id, hasil)

# ----------------- ALUR MOBAPAY -----------------
def proses_order_step1(message):
    uid, zid = parse_id(message.text)
    if not uid:
        bot.send_message(message.chat.id, "❌ Format salah! Harus pakai koma.")
        return
    
    # Tampilkan katalog
    katalog_teks = get_katalog_text()
    msg = bot.send_message(message.chat.id, f"ID tercatat: `{uid} ({zid})`\n\n{katalog_teks}\n👉 *Ketik nomor produk yang ingin dibeli (1-20):*")
    
    # Lanjut ke step 2 sambil membawa data uid dan zid
    bot.register_next_step_handler(msg, proses_order_step2, uid, zid)

def proses_order_step2(message, uid, zid):
    pilihan = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Memproses pembayaran...")
    hasil = eksekusi_order(uid, zid, pilihan)
    bot.send_message(message.chat.id, hasil, disable_web_page_preview=True)

# ----------------- ALUR GOPAY -----------------
def proses_gopay_step1(message):
    uid, zid = parse_id(message.text)
    if not uid:
        bot.send_message(message.chat.id, "❌ Format salah! Harus pakai koma.")
        return
    
    bot.send_message(message.chat.id, "⏳ Mengecek Info Akun & Region ke server GoPay...")
    sukses, teks_akun = cek_akun_gopay(uid, zid)
    
    # Jika akun valid, langsung munculkan Katalog GoPay!
    if sukses:
        katalog_teks = get_katalog_gopay_text()
        pesan = f"{teks_akun}\n\n{katalog_teks}\n👉 *Ketik nomor produk yang ingin dibeli (1-19):*"
        msg = bot.send_message(message.chat.id, pesan)
        # Bawa data UID dan ZID ke step selanjutnya
        bot.register_next_step_handler(msg, proses_gopay_step2, uid, zid)
    else:
        # Jika akun gagal ditemukan, jangan lanjut ke katalog
        bot.send_message(message.chat.id, teks_akun)

def proses_gopay_step2(message, uid, zid):
    pilihan = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Memproses pembuatan link bayar GoPay...")
    hasil = eksekusi_order_gopay(uid, zid, pilihan)
    bot.send_message(message.chat.id, hasil, disable_web_page_preview=True)


# Jalankan Bot
print("Bot sedang berjalan...")
bot.infinity_polling()
