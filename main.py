import subprocess
import time

print("🚀 Memulai jalankan 2 Bot Telegram dalam 1 Server...")

# Panggil bot lama (notif)
proses1 = subprocess.Popen(["python", "bot_notif.py"])

# Panggil bot baru (kasir)
proses2 = subprocess.Popen(["python", "bot_kasir.py"])

try:
    proses1.wait()
    proses2.wait()
except KeyboardInterrupt:
    print("Mematikan semua bot...")
    proses1.terminate()
    proses2.terminate()