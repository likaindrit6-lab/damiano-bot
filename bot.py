import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

ITALY = timezone(timedelta(hours=2))
app = Flask(__name__)
@app.route('/')
def home(): return f"BOT LIVE {datetime.now(ITALY).strftime('%H:%M:%S')}"

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        if r.status_code == 429: return "LIMIT"
        return r.json().get("response", [])
    except: return []

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))

threading.Thread(target=run_web, daemon=True).start()
time.sleep(2)
tg(f"✅ BOT FIXATO - {datetime.now(ITALY).strftime('%H:%M:%S')} - Solo >80% + GOL VINTO")

avvisati = set()
gol_memoria = {}
giorno_reset = datetime.now(ITALY).day
ultimo_golgol = 0
BLACK = ["U23","U21","U19","Women","Youth","Reserve","Amateur","Friendly"]

while True:
    try:
        now_it = datetime.now(ITALY)
        if now_it.day!= giorno_reset:
            avvisati.clear(); gol_memoria.clear(); giorno_reset = now_it.day

        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT":
            tg("⚠️ Limite API pausa 1h"); time.sleep(3600); continue
        if not live:
            time.sleep(60); continue

        if time.time() - ultimo_golgol >= 10800:
            oggi = now_it.strftime("%Y-%
