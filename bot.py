
import os, threading, time, requests
from flask import Flask
from datetime import datetime

print(">>> AVVIO BOT DAMIANO <<<", flush=True)

app = Flask(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@app.route('/')
def home():
    return "Bot V3 Live - OK"

def run_web():
    print("Flask in avvio porta 10000...", flush=True)
    app.run(host="0.0.0.0", port=10000)

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram inviato: {msg[:30]}", flush=True)
    except Exception as e:
        print(f"Errore Telegram: {e}", flush=True)

def get_live():
    try:
        headers = {"x-apisports-key": API_KEY}
        r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=15)
        data = r.json()
        return data.get("response", [])
    except Exception as e:
        print(f"Errore API: {e}", flush=True)
        return []

# AVVIO WEB IN BACKGROUND
threading.Thread(target=run_web, daemon=True).start()
time.sleep(2)

# AVVIO BOT
print(">>> BOT THREAD AVVIATO <<<", flush=True)
send_telegram("✅ *Bot V3 attivo!* - Damiano")

while True:
    try:
        print(f"Controllo fatto {datetime.now().strftime('%H:%M:%S')}", flush=True)
        live = get_live()
        print(f"Partite live: {len(live)}", flush=True)
        # qui va la tua logica di pronostici
        time.sleep(60)
    except Exception as e:
        print(f"Errore loop: {e}", flush=True)
        time.sleep(60)
