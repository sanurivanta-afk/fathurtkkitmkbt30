import requests
import time

# ==========================================
# KATALOG PRODUK MOBAPAY (REGION MY)
# ==========================================
KATALOG_MY = {
    "1": {"nama": "Weekly Diamond Pass", "goods_id": 120991, "amount_pay": 3000000, "price_pay": 3000000, "pay_channel_sub_id": 10079},
    "2": {"nama": "2010 Diamonds", "goods_id": 61, "amount_pay": 50000000, "price_pay": 50000000, "pay_channel_sub_id": 10079},
    "3": {"nama": "4830 Diamonds", "goods_id": 62, "amount_pay": 120000000, "price_pay": 120000000, "pay_channel_sub_id": 10079},
}

GOPAY_COOKIE = "OptanonAlertBoxClosed=2026-04-10T13:17:35.666Z; OptanonConsent=isGpcEnabled=0&datestamp=Mon+May+11+2026+17%3A25%3A59+GMT%2B0700+(Western+Indonesia+Time)&version=202502.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=0b81b4c8-6ee8-474f-b35e-f9f390ba245a&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0004%3A0&intType=3&geolocation=ID%3BSS&AwaitingReconsent=false; i18n_locale=id; _gcl_au=1.1.554417985.1775826869; _ga=GA1.1.335060989.1775826869; _fbp=fb.2.1775826936158.314043899933790245; _tt_enable_cookie=1; _ttp=01KNYC24MKJGQ6M2QGABYJBMQB_.tt.2; _gcl_gs=2.1.k1$i1775958728$u122540957; _gcl_aw=GCL.1775958731.CjwKCAjw4ufOBhBkEiwAfuC7-d6MCYxPRPRhbz_1C00R1IAw-hZECD-23IDHLiew6276gRzTYoj7ixoC8U0QAvD_BwE; slug=mobile-legends-bang-bang; acw_tc=8001b2a817784947706145136edaa0b6dc913f180ece6857a976381f7c; cdn_sec_tc=8001b2a817784947706145136edaa0b6dc913f180ece6857a976381f7c; _ga_BN5XNR85J0=GS2.1.s1778495147$o94$g1$t1778495158$j49$l0$h0; _heatVid_5483=6511172559623000007; _heatIdvUpdated_5483=1778495159623; ttcsid_CSB2C8RC77UFDI754AF0=1778495158725::5ZXy0SL8zro_e2_kPsK9.19.1778495164601.0; ttcsid=1778494769160::AhJ-dgOwFOcxgbriFm4P.32.1778495164601.0::1.385539.389566::396252.52.297.274::373374.26.0"

def get_gopay_headers():
    return {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Cookie": GOPAY_COOKIE,
        "Origin": "https://gopay.co.id",
        "Referer": "https://gopay.co.id/games/mobile-legends-bang-bang",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1 Edg/148.0.0.0",
        "X-Client": "web-mobile",
        "X-Timestamp": str(int(time.time() * 1000)),
        "x-captcha-token": ""
    }

def get_katalog_my_text():
    teks = "🇲🇾 *KATALOG MOBAPAY (MY)* 🇲🇾\n\n"
    for no, prod in KATALOG_MY.items():
        teks += f"*{no}.* {prod['nama']}\n"
    return teks

def cek_region_akun(user_id, zone_id):
    url = "https://gopay.co.id/games/v1/order/user-account"
    payload = {"code": "MOBILE_LEGENDS", "data": {"userId": user_id, "zoneId": zone_id}}

    try:
        res = requests.post(url, json=payload, headers=get_gopay_headers(), timeout=10).json()

        if res.get("message") == "Success" and "data" in res:
            data_akun = res["data"]
            # Filter username biar aman dari bentrok karakter Markdown Telegram
            username = str(data_akun.get("username", "Unknown")).replace("_", "\\_").replace("*", "\\*")
            country_origin = str(data_akun.get("countryOrigin", "")).upper()
            
            if country_origin == "MY":
                pesan = f"✅ *Akun Ditemukan!*\n👤 Username: {username}\n🌍 Region: {country_origin}"
                return True, username, pesan
            else:
                pesan = f"❌ *DITOLAK!*\nAkun ini Region `{country_origin}`.\nFitur ini khusus Region MY!"
                return False, None, pesan
        else:
            return False, None, f"❌ Gagal validasi: {res.get('message')}"
    except Exception as e:
        return False, None, f"⚠️ Error koneksi: {e}"

def eksekusi_order_my(user_id, zone_id, username, pilihan):
    if pilihan not in KATALOG_MY:
        return "❌ Pilihan nomor tidak ada di katalog MY."

    produk = KATALOG_MY[pilihan]
    
    headers_moba = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://www.mobapay.com",
        "Referer": "https://www.mobapay.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
        "X-Lang": "id",
        "X-Mm-Version": "2.13.24"
    }

    url_order = "https://api.mobapay.com/pay/order"
    payload_order = {
        "app_id": 100000, "game_user_key": str(user_id), "game_server_key": str(zone_id),
        "email": "subuhan532@gmail.com", "shop_id": 1022, "amount_pay": produk["amount_pay"],
        "currency_code": "IDR", "country_code": "ID", "goods_id": produk["goods_id"], 
        "num": 1, "pay_channel_sub_id": produk["pay_channel_sub_id"], "price_pay": produk["price_pay"],
        "lang": "id", "network": "", "net": "unipin", "link_key": "net=unipin&r=ID",
        "terminal_type": "WEB", "merchant_return_url": "https://www.mobapay.com/mlbb/?net=unipin&r=ID"
    }

    try:
        res_order = requests.post(url_order, json=payload_order, headers=headers_moba, timeout=15).json()
        
        if res_order.get("code") != 0:
            return f"❌ Gagal membuat order.\nResponse: {res_order}"

        order_id = res_order.get("data", {}).get("order_id")

        url_payment = "https://api.mobapay.com/pay/order/payment"
        payload_payment = {
            "order_id": order_id,
            "return_url": f"https://www.mobapay.com/order?appid=100000&net=unipin&order={order_id}&r=ID",
            "merchant_return_url": "https://www.mobapay.com/mlbb/?net=unipin&r=ID",
            "network": "", "net": "unipin", "terminal_type": "WEB"
        }

        res_pay = requests.post(url_payment, json=payload_payment, headers=headers_moba, timeout=15).json()

        if res_pay.get("code") == 0:
            payment_url = res_pay.get("data", {}).get("payment_url")
            return (f"✅ *ORDER SUKSES!*\n\n"
                    f"👤 Username: {username}\n"
                    f"🛍️ Item: {produk['nama']}\n\n"
                    f"🔗 *Link UniPin:*\n{payment_url}")
        else:
            return f"❌ Gagal dapat link.\nResponse: {res_pay}"
    except Exception as e:
        return f"⚠️ Error sistem Mobapay: {e}"