import os, time, requests, threading
from flask import Flask
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
@app.route('/')
def home(): return "ok"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

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

rossi=set()
avvisati=set()
ultimo=time.time()-7000

while True:
    live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
    if live=="LIMIT":
        time.sleep(3600)
        continue
    for g in live:
        fid=g["fixture"]["id"]
        m=g["fixture"]["status"]["elapsed"] or 0
        gh=g["goals"]["home"]
        ga=g["goals"]["away"]
        if 1<=m<=60 and fid not in rossi:
            ev=api_get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}")
            if ev!="LIMIT":
                for e in ev:
                    if e["type"]=="Card" and e["detail"]=="Red Card" and e["time"]["elapsed"]<=60:
                        tg(f"🟥 ROSSO {e['time']['elapsed']}'\n🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\n👤 {e['player']['name']}")
                        rossi.add(fid)
        if m>=55 and fid not in avvisati:
            perc=80+(2 if m>=60 else 0)+(3 if m>=65 else 0)+(4 if m>=70 else 0)+(3 if m>=75 else 0)
            if perc>92: perc=92
            tg(f"🔥 {m}' >80%\n🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\n<b>Prob: {perc}%</b>")
            avvisati.add(fid)
    if time.time()-ultimo>=7200:
        cand=[]
        for g in live:
            m=g["fixture"]["status"]["elapsed"] or 0
            if m>=55:
                perc=80+(2 if m>=60 else 0)+(3 if m>=65 else 0)+(4 if m>=70 else 0)+(3 if m>=75 else 0)
                if perc>92: perc=92
                cand.append((perc,g))
        cand.sort(key=lambda x:x[0], reverse=True)
        top=cand[:3]
        if top:
            txt=f"🔥 TOP 3 DAL 55' - {datetime.now().strftime('%H:%M')}\n\n"
            for p,gg in top:
                txt+=f"⚽️ {gg['fixture']['status']['elapsed']}' 🌍 {gg['league']['country']} - {gg['league']['name']}\n{gg['teams']['home']['name']} {gg['goals']['home']}-{gg['goals']['away']} {gg['teams']['away']['name']}\n<b>Prob: {p}%</b>\n\n"
            tg(txt)
        ultimo=time.time()
    time.sleep(90)
