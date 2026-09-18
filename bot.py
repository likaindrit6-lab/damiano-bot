
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
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web, daemon=True).start()

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Telegram error: {e}")

def get_live():
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS)
        return r.json().get("response", [])
    except:
        return []

def check_match(fixture):
    status = fixture['fixture']['status']['short']
    elapsed = fixture['fixture']['status']['elapsed']
    if status not in ["1H", "HT"]:
        return False
    if elapsed is None or elapsed < 30 or elapsed > 55:
        return False
    if fixture['goals']['home'] != 1 or fixture['goals']['away'] != 1:
        return False
    return True

send_telegram("✅ *Bot V3 attivo!* Logica 1-1 (30-55')")

while True:
    try:
        for f in get_live():
            if check_match(f):
                home = f['teams']['home']['name']
                away = f['teams']['away']['name']
                el = f['fixture']['status']['elapsed']
                send_telegram(f"🔥 *1-1 TROVATO* {home} vs {away} - {el}'")
        print("Controllo fatto")
    except Exception as e:
        print(e)
    time.sleep(90)
