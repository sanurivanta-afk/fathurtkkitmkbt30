import requests

def cek_promo(user_id, zone_id):
    url = f"https://api.mobapay.com/api/app_shop?app_id=100000&game_user_key={user_id}&game_server_key={zone_id}&country=ID&language=en&network=&net=&coupon_id=&shop_id=1001"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    target_produk = {
        126306: "First Recharge 50 + 50",
        126307: "First Recharge 150 + 150", 
        126315: "First Recharge 250 + 250",
        126316: "First Recharge 500 + 500"
    }

    try:
        response = requests.get(url, headers=headers)
        data_utama = response.json().get("data", {})

        user_info = data_utama.get("user_info", {})
        if user_info.get("code") != 0:
            return "❌ Akun tidak ditemukan di server Mobapay."

        username = user_info.get("user_name", "Tidak terdeteksi")
        hasil = f"👤 *Username:* `{username}`\n🆔 *ID:* `{user_id} ({zone_id})`\n\n*--- STATUS FIRST RECHARGE ---*\n"
        
        shop_info = data_utama.get("shop_info", {})
        shelf_location = shop_info.get("shelf_location", [])
        status_item = {}

        for shelf in shelf_location:
            for barang in shelf.get("goods", []):
                id_barang = barang.get("id")
                if id_barang in target_produk:
                    status_item[id_barang] = str(barang.get("goods_limit", {}).get("reached_limit")).lower()

        ada = False
        for id_barang, nama_produk in target_produk.items():
            status = status_item.get(id_barang)
            if status == "false":
                hasil += f"✅ {nama_produk} : *TERSEDIA*\n"
                ada = True
            elif status == "true":
                hasil += f"❌ {nama_produk} : HABIS\n"
            else:
                hasil += f"⚠️ {nama_produk} : Tidak terdeteksi\n"

        hasil += "\n" + ("ℹ️ *Masih ada kuota Promo!*" if ada else "ℹ️ *Semua kuota Promo sudah habis.*")
        return hasil
    except Exception as e:
        return f"⚠️ Terjadi error sistem: {e}"