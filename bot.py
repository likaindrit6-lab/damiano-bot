import os, time, requests, threading
from flask import Flask
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
@app.route('/')
def home(): return f"Bot Dami Pro 7500 - ID {CHAT_ID} online"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=20)
    except: pass

tg(f"✅ BOT DAMI PRO 7500 ATTIVO\n🌍 Nazione + Campionato\n⚽️ Gol dopo 60' con %\n🟥 Rosso entro 60' subito\n⏰ Top 3 ogni 2 ore\nID {CHAT_ID}")

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        data = r.json()
        if r.status_code == 429 or ("errors" in data and data["errors"]):
            return "LIMIT"
        return data.get("response", [])
    except:
        return []

def calcola_perc(g):
    try:
        m = g["fixture"]["status"]["elapsed"] or 60
        base = 68
        if m >= 65: base += 5
        if m >= 70: base += 7
        if base > 92: base = 92
        return base
    except:
        return 75

rossi_inviati = set()
ultimo_2ore = time.time() - 7200

while True:
    try:
        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")

        if live == "LIMIT":
            tg("⚠️ 7500 finite oggi Pro. Pausa fino alle 02:10 italiane")
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=1)
            midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 10, 0)
            time.sleep((midnight-now).total_seconds())
            continue

        # 1. ROSSO ENTRO 60' SUBITO
        for g in live:
            m = g["fixture"]["status"]["elapsed"] or 0
            fid = g["fixture"]["id"]
            if 1 <= m <= 60 and fid not in rossi_inviati:
                eventi = api_get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}")
                if eventi == "LIMIT": continue
                for ev in eventi:
                    if ev["type"] == "Card" and ev["detail"] == "Red Card" and ev["time"]["elapsed"] <= 60:
                        tg(f"🟥 ROSSO {ev['time']['elapsed']}' entro 60'\n🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} {g['goals']['home']} - {g['goals']['away']} {g['teams']['away']['name']}\n👤 {ev['player']['name']}")
                        rossi_inviati.add(fid)

        # 2. TOP 3 OGNI 2 ORE CON % DOPO 60'
        if time.time() - ultimo_2ore >= 7200:
            cand = []
            for g in live:
                m = g["fixture"]["status"]["elapsed"] or 0
                if m >= 60 and g["goals"]["home"] == 0 and g["goals"]["away"] == 0:
                    cand.append((calcola_perc(g), g))
            cand.sort(key=lambda x: x[0], reverse=True)
            top3 = cand[:3]
            if top3:
                msg = f"🔥 TOP 3 GOL DOPO 60' - {datetime.now().strftime('%H:%M')}\n\n"
                for perc, g in top3:
                    m = g["fixture"]["status"]["elapsed"]
                    msg += f"⚽️ {m}' 🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} 0-0 {g['teams']['away']['name']}\n<b>Prob. gol dopo 60': {perc}%</b>\n\n"
                tg(msg)
            ultimo_2ore = time.time()

        time.sleep(300) # 5 minuti

    except Exception as e:
        print(e)
        time.sleep(300)
