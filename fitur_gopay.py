import requests
import time

# ==========================================
# KREDENSIAL GOPAY (Update jika error 406)
# ==========================================
COOKIE = "OptanonAlertBoxClosed=2026-02-07T14:47:47.909Z; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Mar+27+2026+10%3A42%3A31+GMT%2B0700+(Western+Indonesia+Time)&version=202502.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=dbf6d8c9-6de1-4b1b-aaca-c5708c18814e&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1&intType=1&geolocation=ID%3BSS&AwaitingReconsent=false; _gcl_au=1.1.1727386525.1770475659; _gac_UA-192981135-1=1.1770475663.Cj0KCQiA4pvMBhDYARIsAGfgwvwS2un3ULPuU7mLoJvvII8tuZT7G-WTNWqo1uLgpzbc1ifzw7ICqOQaAtHtEALw_wcB; _tt_enable_cookie=1; _ttp=01KGW95BYBDKV7Z3126PAAJBKG_.tt.2; _fbp=fb.2.1770475663635.825830333120119577; i18n_locale=id; ttcsid=1770475663309::g8GjJbbqZqyhrn6Eoavm.1.1770476776867.0; ttcsid_CSB2C8RC77UFDI754AF0=1770475663309::E3voX5886iqGMAzEvSh2.1.1770476776867.1; ttcsid_C5VSGL8QCDCTJUG0EQL0=1770475668449::p2diyOHu-zoyVwvnTOcp.1.1770476776867.1; _ga=GA1.1.2088880486.1770475659; slug=mobile-legends-bang-bang; acw_tc=9581d31e17745826366588015ed2895012c91264d6c73889d1ea432e268fc8; _gcl_gs=2.1.k1$i1774582949$u122540957; _gcl_aw=GCL.1774582951.CjwKCAjwspPOBhB9EiwATFbi5H3nGTfvgdR0KVE3PDxkEypUnDsb3TGUs_nZLoH-PH5K37YJQQzBEhoCI-8QAvD_BwE; _ga_BN5XNR85J0=GS2.1.s1774580835$o3$g1$t1774582962$j48$l0$h0"

X_CAPTCHA_TOKEN = "0cAFcWeA7H0lBeJEjKsLYp9QLlrXvFPb_mWJic2r1td7gXbO3ajVuQ4-ei7urnS3-DJeVWrNmBtZKGzBx7ObVL5wW_cAbRKan6iAeUHMnf4D-aGaB6ID_wHUCy22bE6XaeiTCCMWhhhhF0R29GPEZ-D_nxK8latmvXWzlBAqrJpjhkmLLhzBA_x25dzbIj-o6wexo-AQcnYnocrR8prNl7sEHdstl5NqylfhxH7mogzfLAo6040iNb8O8L2ZzmP31H3x8j5HplhL_TZFydhzmInT9mjme9c2NWrs21xIGKgPRuXbYlT9Z8bxehOxFphe3UfmV2ZtZ2NKKoLgMjj7S21Mh-NmSCAVTdm0IN2DWZDT5ZSb_sv2orIx_wvRKHGbHw5z65ouS_FJ5M98UORDQV_foU5dz5gwi5hNzGfOCplfStCcN2LI8iiTXIteX8dlY6XiMuAAHxqO_zMo4qE1Cbk_OSC1JjoONP8kDI3XBnYmUv4k2FT20Cep0bqMBjq5FTswZTZ72Vagro54CRIcsKqXQxdxlGsYEtrpSWkTOUkEA1PckL1GA0p_parvAY6M7sTgMMmj8gHOgx74vqRjRvs0HIdAhtNEbTpfmfl1BcmptGy2IpYglAGjaAIklleAGC1mATXG_7N5DASEVrzFh35ltW_MxrXxdmrvjqpVHhtkkLoduIrhzoNX1qzmj-iSmKy-LBvLavsodzh2bb838IPGEw9vJbZgQ8kbWUrfym1sdk3CWzfigjakpDJdNSBYNM0GrKM3fzQhd5JRwrKPUQZlhKtYtLFmrzU9OBTW9nZujnoywRny4rHy6eXk3yeTtwTTYEd8UvJ-S-fY8n5ZW0nptFQ8dnk5abA_2m85Neciy6s0zQUVIsASxD36650Rwl9RVH40S0Asjf_Wb7ULItSCrKSzk4JI9iCCZ0WqzDRhjs8RPai9gewn8PQ05Vyh_7f_bJgHOvg_dEA4B7uovvnH7-qpJPk9ue6JF6dJ8JqxJqAfVhtzDRQ2nXt3pDAOOG3tW8Jm_d6l6H8V6Ewn9sBVgNGcaNt20I5-MKAXpklNJwIr3ifXYAtmMG6kPc4rdjEYBmML4-a76ACnKE4ryAIVHbXaeWFtW2pASrAL9gKImMmSobtYvBls2DsAgXFJwufyUehHtCvAqEgScojqoImvM92usqwtaYa8-JGKpPKYhrev3GWyHdAGwBFAeTLKQCZ_2a8gMOex-eVUVR6qtJMB-goF04-to4XaHYJgare1Lim1f1yX5FzgPqoDTmxbouVTJbXlVtxVzctfgkANQxJPcj5IIkfOjRizchPybM5ameMcaIiX3ekgTBdv7Mf21ILCfaV-TWcTbUcIMtFjpjX_yFeaTfTSxL2cRlcCjjIGxNB3cY8eXLPxs2ZuvP6UKjjqAu8NgrhAzagzQ_pa9ZMS5gbsTvg-eZYXsy6_N58aAqYnyZpplBe8qJNBSwsMVKZPa_ghi8SWAXEmKzvmY4rOsnyNhtkk07467FOeoryBFALi2wXcNt9_E0VfEGe9qxf-wf411XudfGvc8RQa0Wf0mgAJqq_zDziI42E6bfLkrsVrqlXh_XUY7XRAaJEer4_wTvizHz1Qwx73QT3WnSpkmSL9WUAPviJsStprNyAq9SWTwjBovqnmS0NOHlMFRWiIRTq-U2cNtjdS5gz1t80-W2skxTx8QYpWrVVFdgAPeqXX8pn_q-3gZwaIp2-P3d2RlDaCUdTNu16LG0QY2f4dAj5tQ7KUasoHsUM-0gtoyOtmSViMSfSjkOwPzOB47ly4vDGQgmoIjvQfQb2XKDYy2kPz4soV4iJpWxonnumUkJxc-JDB4e7NNiy8IV7TPix_NKzNOwxix31AS-nWjTgBrdt8GScsxyYXbqsuV_VvWfOR3yuV5sSJnVSciCZk3gLGd1jP6tdlYK57LYggPymlrt0In-bfc4WTUd0hW-b1PEOqdTDL2zvJiTDBYy858olQ7ihFkKbeox4cjE9evpGshgGsskMVNQ4nVM7eSCzOXBO6fPZYLH5qnEH59ajANnlucDNqIxJNmFyHct7sCg6jCr5wakd8XcZvThqtapCLXkTX25qCPQ7rEHqeeLZwe2idc_OvqhLuqXvs8Qx8AwA0xysljl7u3iG-KfFo7v9eNF2Zev2EZXbUae7cybcPy9J0CqfJfdAQwEVnyapDupSM-cr2znDevrZhe3Q6eKLwIpY0vKpPcjSOfyYPv1vRVWXY2FQHlexmwfmSTswsZwjcEO_1GBWJpL7rw-vqWKkq0H-h2DsdsKYoaZ-toaI_cJyze0zbhK6Wfj"

# ==========================================
# KATALOG PRODUK GOPAY (Diubah jadi format nomor)
# ==========================================
katalog_gopay = {
    "1": {"nama": "5 Diamonds", "item_id": 358},
    "2": {"nama": "10 Diamonds", "item_id": 419},
    "3": {"nama": "28 Diamonds", "item_id": 420},
    "4": {"nama": "44 Diamonds", "item_id": 362},
    "5": {"nama": "54 Diamonds", "item_id": 425},
    "6": {"nama": "128 Diamonds", "item_id": 427},
    "7": {"nama": "148 Diamonds", "item_id": 429},
    "8": {"nama": "284 Diamonds", "item_id": 418},
    "9": {"nama": "346 Diamonds", "item_id": 465},
    "10": {"nama": "424 Diamonds", "item_id": 468},
    "11": {"nama": "452 Diamonds", "item_id": 458},
    "12": {"nama": "642 Diamonds", "item_id": 435},
    "13": {"nama": "716 Diamonds", "item_id": 382},
    "14": {"nama": "966 Diamonds", "item_id": 421},
    "15": {"nama": "999 Diamonds (Weekly Pass)", "item_id": 366},
    "16": {"nama": "1045 Diamonds", "item_id": 452},
    "17": {"nama": "1443 Diamonds", "item_id": 453},
    "18": {"nama": "2010 Diamonds", "item_id": 424},
    "19": {"nama": "4830 Diamonds", "item_id": 423},
}

def get_headers_gopay():
    """Mengumpulkan headers dinamis untuk GoPay"""
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "cookie": COOKIE,
        "origin": "https://gopay.co.id",
        "referer": "https://gopay.co.id/games/mobile-legends-bang-bang",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-captcha-token": X_CAPTCHA_TOKEN,
        "x-client": "mobile",
        "x-timestamp": str(int(time.time() * 1000))
    }

def get_katalog_gopay_text():
    teks = "*--- KATALOG GOPAY ---*\n"
    for no, prod in katalog_gopay.items():
        teks += f"*{no}.* {prod['nama']}\n"
    return teks

def cek_akun_gopay(user_id, zone_id):
    """Mengecek Username & Region sebelum order"""
    url = "https://gopay.co.id/games/v1/order/user-account"
    payload = {
        "code": "MOBILE_LEGENDS",
        "data": {
            "userId": str(user_id),
            "zoneId": str(zone_id)
        }
    }

    try:
        res = requests.post(url, json=payload, headers=get_headers_gopay(), timeout=15)
        data_response = res.json()

        if data_response.get("message") == "Success" and "data" in data_response:
            data_akun = data_response["data"]
            username = str(data_akun.get("username", "Tidak diketahui")).replace("_", "\\_").replace("*", "\\*")
            country_origin = str(data_akun.get("countryOrigin", "??")).upper()
            
            hasil = (f"✅ *Akun Ditemukan!*\n"
                     f"👤 Username : {username}\n"
                     f"🆔 ID Akun  : {user_id} ({zone_id})\n"
                     f"🌍 Region   : {country_origin}")
            return True, hasil
        else:
            return False, f"❌ Akun tidak ditemukan atau ID/Server salah.\nInfo: {data_response.get('message')}"
    except Exception as e:
        return False, f"⚠️ Terjadi error koneksi: {e}"

def eksekusi_order_gopay(user_id, zone_id, pilihan):
    """Membuat Order & Mendapatkan URL Pembayaran via GoPay"""
    if pilihan not in katalog_gopay:
        return "❌ Pilihan nomor tidak ada di katalog GoPay."

    produk = katalog_gopay[pilihan]
    headers = get_headers_gopay()
    
    # TAHAP 1: Inquiry
    inquiry_url = "https://gopay.co.id/games/v1/order/inquiry"
    inquiry_payload = {
        "productId": 19,
        "productItemId": produk["item_id"],
        "data": {
            "userId": str(user_id),
            "zoneId": str(zone_id)
        },
        "paymentChannelId": 73,
        "phoneNumber": "628783219212", 
        "voucher": "",
        "referralCode": "",
        "paymentPhoneNumber": "",
        "quantity": 1
    }

    try:
        resp1 = requests.post(inquiry_url, json=inquiry_payload, headers=headers, timeout=15)
        data_inquiry = resp1.json()
        
        if data_inquiry.get("message") != "Confirm Payment":
            return f"❌ Gagal membuat order (Mungkin Limit / Token Kadaluarsa).\nInfo: {data_inquiry.get('message')}"
        
        order_id = data_inquiry["data"]["orderId"]

        # TAHAP 2: Request URL Pembayaran
        payment_url = "https://gopay.co.id/games/v1/order/payment"
        payment_payload = {
            "orderId": order_id,
            "paymentChannelId": 73,
            "phoneNumber": "628783219212",
            "paymentPhoneNumber": "",
            "quantity": 1,
            "invoiceUrl": "https://gopay.co.id/games/payment/"
        }

        resp2 = requests.post(payment_url, json=payment_payload, headers=get_headers_gopay(), timeout=15)
        data_payment = resp2.json()

        if data_payment.get("message") == "Success Order":
            payment_token = data_payment["data"]
            link_final = f"https://gopay.co.id/games/payment/{payment_token}"
            
            return (f"✅ *ORDER GOPAY BERHASIL!*\n\n"
                    f"🛍️ Item: {produk['nama']}\n\n"
                    f"🔗 *Link Bayar:*\n{link_final}")
        else:
            return f"❌ Gagal memuat halaman pembayaran.\nInfo: {data_payment.get('message')}"

    except Exception as e:
        return f"⚠️ Terjadi error sistem GoPay: {e}"