import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

ITALY = timezone(timedelta(hours=2))
app = Flask(__name__)
@app.route('/')
def home(): return "BOT LIVE OK"

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
tg("✅ BOT 55' 80%+ TUTTE LE LEGHE ATTIVO")

avvisati = set()

while True:
    try:
        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT":
            tg("⚠️ Limite API pausa 1h"); time.sleep(3600); continue
        if not live:
            time.sleep(60); continue

        for g in live:
            fid = g["fixture"]["id"]
            m = g["fixture"]["status"]["elapsed"] or 0
            lega = g["league"]["name"]
            country = g["league"]["country"]
            home = g["teams"]["home"]["name"]
            away = g["teams"]["away"]["name"]
            gh = g["goals"]["home"]; ga = g["goals"]["away"]

            # NESSUN FILTRO CATEGORIE - TUTTE LE LEGHE BUONE

            # SOLO DAL 55' IN POI
            if m < 55 or m > 88: continue

            # PERCENTUALE
            perc = 80
            if m >= 65: perc = 85
            if m >= 75: perc = 90
            if m >= 80: perc = 92

            # SOLO 80% IN SU - TUTTE QUELLE CHE CI SONO
            if perc < 80: continue
            if fid in avvisati: continue

            tg(f"🔥 {m}' >{perc}%\n🌍 {country} - {lega}\n{home} {gh}-{ga} {away}")
            avvisati.add(fid)

        time.sleep(60)
    except Exception as e:
        tg(f"❌ ERRORE {e}")
        time.sleep(30)
