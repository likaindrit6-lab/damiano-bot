
import os
import time
import requests
import threading
from flask import Flask

API_KEY = os.getenv("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot V3 Live - OK"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Errore Telegram: {e}")

def get_live():
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except:
        return []

def check_match(fixture):
    status = fixture['fixture']['status']['short']
    elapsed = fixture['fixture']['status']['elapsed']
    if status not in ["1H", "2H", "HT"]:
        return False
    if elapsed is None or elapsed < 30 or elapsed > 65:
        return False
    if fixture['goals']['home'] != 1 or fixture['goals']['away'] != 1:
        return False
    return True

# --- AVVIO CORRETTO PER RENDER ---
threading.Thread(target=run_web, daemon=True).start()

send_telegram("✅ *Bot V3 attivo!* Logica 1-1 al 30' - Damiano")

while True:
    try:
        for f in get_live():
            if check_match(f):
                home = f['teams']['home']['name']
                away = f['teams']['away']['name']
                el = f['fixture']['status']['elapsed']
                send_telegram(f"🔥 *1-1 TROVATA!* {home} - {away} al {el}'")
        print("Controllo fatto")
    except Exception as e:
        print(e)
    time.sleep(90)
