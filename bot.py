import os, time, requests, threading
from flask import Flask
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Dami online"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        j = r.json()
        # Controllo VERO del limite
        if r.status_code == 429:
            print("LIMIT 429")
            return "LIMIT"
        if "errors" in j and j["errors"] and "limit" in str(j["errors"]).lower():
            print(f"LIMIT errors: {j['errors']}")
            return "LIMIT"
        return j.get("response", [])
    except Exception as e:
        print(f"Errore: {e}")
        return []

print("=== AVVIO BOT DAMI ===")
tg(f"✅ BOT DAMI PARTITO ORA - 403/7500 usate - ID {CHAT_ID}")

rossi = set()
ultimo = time.time() - 7000

while True:
    live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
    if live == "LIMIT":
        tg("⏸️ Raggiunto limite 7500, pausa fino alle 02:10")
        time.sleep(3600)
        continue

    print(f"{datetime.now().strftime('%H:%M:%S')} - Live: {len(live)}")

    # ROSSO
    for g in live:
        m = g["fixture"]["status"]["elapsed"] or 0
        fid = g["fixture"]["id"]
        if 1 <= m <= 60 and fid not in rossi:
            ev = api_get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}")
            if ev == "LIMIT": continue
            for e in ev:
                if e["type"]=="Card" and e["detail"]=="Red Card" and e["time"]["elapsed"]<=60:
                    tg(f"🟥 ROSSO {e['time']['elapsed']}'\n🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n👤 {e['player']['name']}")
                    rossi.add(fid)

    # TOP 3 ogni 2 ore
    if time.time() - ultimo >= 7200:
        cand=[]
        for g in live:
            m=g["fixture"]["status"]["elapsed"] or 0
            if m>=60 and g["goals"]["home"]==0 and g["goals"]["away"]==0:
                perc = 68 + (5 if m>=65 else 0) + (7 if m>=70 else 0)
                if perc>92: perc=92
                cand.append((perc,g))
        cand.sort(key=lambda x:x[0], reverse=True)
        top=cand[:3]
        if top:
            txt=f"🔥 TOP 3 GOL DOPO 60' - {datetime.now().strftime('%H:%M')}\n\n"
            for p,g in top:
                txt+=f"⚽️ {g['fixture']['status']['elapsed']}' 🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} 0-0 {g['teams']['away']['name']}\n<b>Prob: {p}%</b>\n\n"
            tg(txt)
        ultimo=time.time()
    time.sleep(300)
