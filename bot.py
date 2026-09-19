
import os
import time
import requests
from threading import Thread
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot di Damiano ONLINE!"

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        r = requests.post(url, data=data, timeout=10)
        print(f"Inviato: {r.status_code}")
        return True
    except Exception as e:
        print(f"Errore: {e}")
        return False

def bot_logic():
    time.sleep(5)
    send_telegram("✅ *Bot di Damiano ACCESO!*\nSe leggi questo, funziona!")

    while True:
        time.sleep(120)

if __name__ == "__main__":
    Thread(target=bot_logic, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
