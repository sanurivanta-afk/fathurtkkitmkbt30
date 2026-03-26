import requests

def cek_region(user_id, zone_id):
    url = "https://gopay.co.id/games/v1/order/user-account"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "code": "MOBILE_LEGENDS",
        "data": {"userId": user_id, "zoneId": zone_id}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data_response = response.json()

        if data_response.get("message") == "Success" and "data" in data_response:
            data_akun = data_response["data"]
            username = data_akun.get("username", "Tidak diketahui")
            country_origin = data_akun.get("countryOrigin", "Tidak diketahui").upper()
            
            hasil = (f"✅ *Akun Ditemukan!*\n"
                     f"👤 Username : `{username}`\n"
                     f"🆔 ID Akun  : `{user_id} ({zone_id})`\n"
                     f"🌍 Region   : `{country_origin}`")
            return hasil
        else:
            return f"❌ Akun tidak ditemukan atau ID/Server salah."
    except Exception as e:
        return f"⚠️ Terjadi error sistem: {e}"