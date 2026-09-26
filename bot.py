import os, time, requests, threading
from flask import Flask
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
@app.route('/')
def home(): return "ok"

def tg(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        j = r.json()
        if r.status_code == 429: return "LIMIT"
        if "errors" in j and j["errors"] and "limit" in str(j["errors"]).lower(): return "LIMIT"
        return j.get("response", [])
    except: return []

# FIX CONSUMI
avvisati = set()
giorno_reset = datetime.now().day
ultimo_top = time.time() - 7000

# Flask separato, non dentro il loop
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

while True:
    # Reset giornaliero avvisati
    if datetime.now().day!= giorno_reset:
        avvisati.clear()
        giorno_reset = datetime.now().day
        tg(f"🔄 Reset giorno {giorno_reset}")

    live = api_get("https://v3.football.api-sports.io/fixtures?live=all")

    if live == "LIMIT":
        tg("⚠️ Limite API raggiunto, pausa 1h")
        time.sleep(3600)
        continue

    if not live:
        print(f"{datetime.now().strftime('%H:%M')} 0 live")
        time.sleep(120)
        continue

    print(f"{datetime.now().strftime('%H:%M')} LIVE: {len(live)}")

    for g in live:
        fid = g["fixture"]["id"]
        m = g["fixture"]["status"]["elapsed"] or 0
        if m < 55: continue
        if fid in avvisati: continue

        gh = g["goals"]["home"]
        ga = g["goals"]["away"]
        perc = 80 + (2 if m>=60 else 0) + (3 if m>=65 else 0) + (4 if m>=70 else 0) + (3 if m>=75 else 0)
        if perc > 92: perc = 92

        tg(f"🔥 {m}' >80%\n🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\n<b>Prob: {perc}%</b>")
        avvisati.add(fid)

    # TOP 3 ogni 2 ore
    if time.time() - ultimo_top >= 7200:
        cand = []
        for g in live:
            m = g["fixture"]["status"]["elapsed"] or 0
            if m >= 55:
                perc = 80 + (2 if m>=60 else 0) + (3 if m>=65 else 0) + (4 if m>=70 else 0) + (3 if m>=75 else 0)
                cand.append((perc, g))
        cand.sort(key=lambda x: x[0], reverse=True)
        top = cand[:3]
        if top:
            txt = f"🔥 TOP 3 DAL 55' - {datetime.now().strftime('%H:%M')}\n\n"
            for p, gg in top:
                txt += f"⚽️ {gg['fixture']['status']['elapsed']}' 🌍 {gg['league']['country']} - {gg['league']['name']}\n{gg['teams']['home']['name']} {gg['goals']['home']}-{gg['goals']['away']} {gg['teams']['away']['name']}\n<b>Prob: {p}%</b>\n\n"
            tg(txt)
        ultimo_top = time.time()

    time.sleep(120) # 120 sec = 720 richieste al giorno = 9,6% del tuo piano
