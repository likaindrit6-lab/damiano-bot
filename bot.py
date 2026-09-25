import os, time, requests, threading
from flask import Flask
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Dami 606420824 ON"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=15)
    except: pass

# Messaggio solo 1 volta al giorno per non spammare
tg(f"✅ BOT COMPLETO ATTIVO - TUTTO IL MONDO\nID {CHAT_ID} collegato con BOT_TOKEN")

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
            tg("⚠️ 100 API finite, riprendo alle 02:10 italiane")
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=1)
            midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 10, 0)
            time.sleep((midnight-now).total_seconds())
            continue

        if len(res) == 0:
            # Se non ci sono partite live, dorme 15 minuti e non consuma API
            time.sleep(900)
        else:
            for g in res:
                minute = g["fixture"]["status"]["elapsed"] or 0
                if 10 <= minute <= 75:
                    home = g["goals"]["home"]; away = g["goals"]["away"]
                    if home==0 and away==0:
                        tg(f"🔥 {minute}' {g['league']['name']}\n{g['teams']['home']['name']} 0-0 {g['teams']['away']['name']}\n<b>Gol: 75% fino al 75'</b>")
            time.sleep(600) # con partite live controlla ogni 10 min = risparmi API

    except:
        time.sleep(600)
