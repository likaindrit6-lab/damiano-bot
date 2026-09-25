import os, time, requests, threading
from flask import Flask
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Dami ON"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

def tg(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=15)

tg(f"✅ Dami fatto! ID {CHAT_ID} collegato.\nDa ora uso BOT_TOKEN come hai detto tu")

def get_live():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20).json()
    if "errors" in r and r["errors"] and "limit" in str(r["errors"]).lower():
        return "LIMIT"
    return r.get("response", [])

while True:
    try:
        res = get_live()
        if res == "LIMIT":
            tg("⚠️ 100 API finite, riprendo alle 02:10")
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=1)
            midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 10, 0)
            time.sleep((midnight-now).total_seconds())
            continue
        for g in res:
            minute = g["fixture"]["status"]["elapsed"] or 0
            if 10 <= minute <= 75 and g["goals"]["home"]==0 and g["goals"]["away"]==0:
                tg(f"🔥 {minute}' {g['league']['name']}\n{g['teams']['home']['name']} 0-0 {g['teams']['away']['name']}\n<b>Gol: 75%</b>")
    except: pass
    time.sleep(300)
