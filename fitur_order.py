import requests
from datetime import datetime

katalog = {
    "1": {"nama": "First Recharge 50 + 50", "goods_id": 126306, "amount_pay": 1405300, "price_pay": 1405300, "pay_channel_sub_id": 125325, "shelf_index": 2},
    "2": {"nama": "First Recharge 150 + 150", "goods_id": 126307, "amount_pay": 4191900, "price_pay": 4191900, "pay_channel_sub_id": 123449, "shelf_index": 2},
    "3": {"nama": "First Recharge 250 + 250", "goods_id": 126315, "amount_pay": 6988900, "price_pay": 6988900, "pay_channel_sub_id": 123449, "shelf_index": 2},
    "4": {"nama": "First Recharge 500 + 500", "goods_id": 126316, "amount_pay": 14053000, "price_pay": 14053000, "pay_channel_sub_id": 121430, "shelf_index": 2},
    "5": {"nama": "First Recharge 25 + 25", "goods_id": 121285, "amount_pay": 752000, "price_pay": 752000, "pay_channel_sub_id": 123449},
    "6": {"nama": "5 Diamonds", "goods_id": 48, "amount_pay": 141000, "price_pay": 141000, "pay_channel_sub_id": 123449},
    "7": {"nama": "11+1 Diamonds", "goods_id": 49, "amount_pay": 329000, "price_pay": 329000, "pay_channel_sub_id": 123449},
    "8": {"nama": "17+2 Diamonds", "goods_id": 50, "amount_pay": 517000, "price_pay": 517000, "pay_channel_sub_id": 123449},
    "9": {"nama": "25+3 Diamonds", "goods_id": 51, "amount_pay": 752000, "price_pay": 752000, "pay_channel_sub_id": 123449},
    "10": {"nama": "40+4 Diamonds", "goods_id": 52, "amount_pay": 1128000, "price_pay": 1128000, "pay_channel_sub_id": 121430},
    "11": {"nama": "53+6 Diamonds", "goods_id": 53, "amount_pay": 1504000, "price_pay": 1504000, "pay_channel_sub_id": 123449},
    "12": {"nama": "77+8 Diamonds", "goods_id": 54, "amount_pay": 2162000, "price_pay": 2162000, "pay_channel_sub_id": 123449},
    "13": {"nama": "154+16 Diamonds", "goods_id": 55, "amount_pay": 4324000, "price_pay": 4324000, "pay_channel_sub_id": 123449},
    "14": {"nama": "217+23 Diamonds", "goods_id": 56, "amount_pay": 6110000, "price_pay": 6110000, "pay_channel_sub_id": 125325},
    "15": {"nama": "256+40 Diamonds", "goods_id": 57, "amount_pay": 7520000, "price_pay": 7520000, "pay_channel_sub_id": 125325},
    "16": {"nama": "367+41 Diamonds", "goods_id": 58, "amount_pay": 10340000, "price_pay": 10340000, "pay_channel_sub_id": 123449},
    "17": {"nama": "503+65 Diamonds", "goods_id": 59, "amount_pay": 14100000, "price_pay": 14100000, "pay_channel_sub_id": 123449},
    "18": {"nama": "774+101 Diamonds", "goods_id": 60, "amount_pay": 21620000, "price_pay": 21620000, "pay_channel_sub_id": 123449},
    "19": {"nama": "1708+302 Diamonds", "goods_id": 61, "amount_pay": 47000000, "price_pay": 47000000, "pay_channel_sub_id": 123449},
    "20": {"nama": "Weekly Diamond Pass", "goods_id": 120991, "amount_pay": 2700000, "price_pay": 2700000, "pay_channel_sub_id": 123449}
}

HEADERS_MOBAPAY = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.mobapay.com",
    "Referer": "https://www.mobapay.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "X-Lang": "id",
    "X-Mm-Version": "2.13.16"
}

def get_katalog_text():
    teks = "*--- KATALOG MOBAPAY ---*\n"
    for no, prod in katalog.items():
        harga = int(prod['price_pay'] / 100)
        teks += f"*{no}.* {prod['nama']} - Rp {harga:,}\n".replace(",", ".")
    return teks

def eksekusi_order(user_id, zone_id, pilihan):
    if pilihan not in katalog:
        return "❌ Pilihan produk tidak valid."

    produk = katalog[pilihan]
    
    payload_order = {
        "app_id": 100000, 
        "game_user_key": user_id, 
        "game_server_key": zone_id,
        "email": "zchange19@gmail.com", 
        "shop_id": 1001, 
        "currency_code": "IDR",
        "country_code": "ID", 
        "num": 1, 
        "lang": "id", 
        "network": "", 
        "net": "",     
        "terminal_type": "WEB",
        "merchant_return_url": "https://www.mobapay.com/mlbb/?r=ID",
        "goods_id": produk["goods_id"], 
        "amount_pay": produk["amount_pay"],
        "price_pay": produk["price_pay"], 
        "pay_channel_sub_id": produk["pay_channel_sub_id"]
    }
    if "shelf_index" in produk:
        payload_order["shelf_index"] = produk["shelf_index"]

    try:
        res_order = requests.post("https://api.mobapay.com/pay/order", json=payload_order, headers=HEADERS_MOBAPAY).json()
        if res_order.get("code") != 0:
            # Format aman tanpa markdown
            return f"❌ Gagal buat order.\nResponse: {res_order}"

        order_id = res_order["data"]["order_id"]
        username = res_order["data"]["user_name"]
        
        # Amanin username (kalau ada pembeli pakai nama aneh-aneh)
        username_aman = str(username).replace("_", "\\_").replace("*", "\\*")

        payload_payment = {
            "order_id": order_id, 
            "return_url": f"https://www.mobapay.com/order?appid=100000&order={order_id}&r=ID",
            "merchant_return_url": "https://www.mobapay.com/mlbb/?r=ID",
            "network": "", 
            "net": "",     
            "terminal_type": "WEB"
        }
        res_pay = requests.post("https://api.mobapay.com/pay/order/payment", json=payload_payment, headers=HEADERS_MOBAPAY).json()
        
        if res_pay.get("code") == 0:
            payment_url = res_pay["data"]["payment_url"]
            waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            riwayat = f"[{waktu}] Order ID: {order_id} | Akun: {username} | Item: {produk['nama']} | URL: {payment_url}\n"
            
            with open("riwayat_pembayaran.txt", "a") as f:
                f.write(riwayat)
                
            # Teks balasan ke bot dibikin se-aman mungkin dari error Parse Entity
            return (f"✅ *ORDER BERHASIL!*\n\n"
                    f"👤 Akun: {username_aman}\n"
                    f"🛍️ Item: {produk['nama']}\n\n"
                    f"🔗 *Link Bayar:*\n{payment_url}\n\n"
                    f"📝 Data tersimpan di riwayat pembukuan.")
        else:
            return f"❌ Gagal mendapatkan URL pembayaran.\nInfo Server: {res_pay}"
    except Exception as e:
        return f"⚠️ Error sistem: {e}"
