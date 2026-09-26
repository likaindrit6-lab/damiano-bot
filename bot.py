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

avvisati = set()
giorno_reset = datetime.now().day
ultimo_top = time.time() - 3000 # parte dopo 10 min
ultima_schedina = 0 # parte SUBITO

def build_schedina(live_list):
    cand = []
    for g in live_list:
        m = g["fixture"]["status"]["elapsed"] or 0
        if not (15 <= m <= 50): continue
        gh = g["goals"]["home"]; ga = g["goals"]["away"]
        if abs(gh-ga) > 1: continue
        if gh + ga > 2: continue
        prob = 70 + (5 if m>=25 else 0) + (5 if m>=35 else 0) + (8 if gh==ga else 0) + (5 if gh+ga==0 else 0)
        quota = 1.28 if prob > 80 else 1.22
        cand.append((prob, quota, g))
    cand.sort(key=lambda x: x[0], reverse=True)
    return cand[:3]

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

while True:
    if datetime.now().day!= giorno_reset:
        avvisati.clear(); giorno_reset = datetime.now().day
        tg(f"🔄 Reset giorno {giorno_reset}")

    live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
    if live == "LIMIT":
        tg("⚠️ Limite API, pausa 1h"); time.sleep(3600); continue
    if not live:
        time.sleep(120); continue

    # 1) DAL 55'
    for g in live:
        fid = g["fixture"]["id"]; m = g["fixture"]["status"]["elapsed"] or 0
        if m < 55 or fid in avvisati: continue
        gh = g["goals"]["home"]; ga = g["goals"]["away"]
        perc = 80 + (2 if m>=60 else 0) + (3 if m>=65 else 0) + (4 if m>=70 else 0) + (3 if m>=75 else 0)
        if perc > 92: perc = 92
        tg(f"🔥 {m}' >80%\n🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\n<b>Prob: {perc}%</b>")
        avvisati.add(fid)

    # 2) TOP 3 OGNI 1 ORA
    if time.time() - ultimo_top >= 3600:
        cand = [(80 + (2 if (g["fixture"]["status"]["elapsed"] or 0)>=60 else 0) + (3 if (g["fixture"]["status"]["elapsed"] or 0)>=65 else 0) + (4 if (g["fixture"]["status"]["elapsed"] or 0)>=70 else 0) + (3 if (g["fixture"]["status"]["elapsed"] or 0)>=75 else 0), g) for g in live if (g["fixture"]["status"]["elapsed"] or 0) >= 55]
        cand.sort(key=lambda x: x[0], reverse=True)
        top = cand[:3]
        if top:
            txt = f"🔥 TOP 3 DAL 55' - {datetime.now().strftime('%H:%M')}\n\n"
            for p, gg in top:
                txt += f"⚽️ {gg['fixture']['status']['elapsed']}' 🌍 {gg['league']['country']} - {gg['league']['name']}\n{gg['teams']['home']['name']} {gg['goals']['home']}-{gg['goals']['away']} {gg['teams']['away']['name']}\n<b>Prob: {min(p,92)}%</b>\n\n"
            tg(txt)
        ultimo_top = time.time()

    # 3) SCHEDINA 1.50 OGNI 60 MIN - SUBITO
    if time.time() - ultima_schedina >= 3600:
        picks = build_schedina(live)
        if len(picks) >= 2:
            quota_tot = 1.0; txt = f"🎫 SCHEDINA 1.50 LIVE - {datetime.now().strftime('%H:%M')}\nDal 15' al 50' - Prossimo Gol\n\n"
            for prob, q, gg in picks:
                quota_tot *= q; m = gg['fixture']['status']['elapsed']
                txt += f"⚽️ {m}' {gg['teams']['home']['name']} {gg['goals']['home']}-{gg['goals']['away']} {gg['teams']['away']['name']}\n👉 Prossimo Gol | {prob}% @ {q}\n🌍 {gg['league']['name']}\n\n"
                if quota_tot >= 1.50: break
            txt += f"💰 QUOTA TOT: {quota_tot:.2f}"
            if quota_tot >= 1.45: tg(txt)
        ultima_schedina = time.time()

    time.sleep(120)
