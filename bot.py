import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

ITALY = timezone(timedelta(hours=2))
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT LIVE OK"

def tg(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=20
        )
    except:
        pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        if r.status_code == 429:
            return "LIMIT"
        data = r.json()
        return data.get("response", [])
    except:
        return []

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
time.sleep(2)
tg("BOT BASE ATTIVO")

avvisati = set()
gol_memoria = {}
giorno_reset = datetime.now(ITALY).day
ultimo_golgol = 0
BLACK = ["U23","U21","U19","Women","Youth","Reserve","Amateur","Friendly"]

while True:
    try:
        now_it = datetime.now(ITALY)
        if now_it.day!= giorno_reset:
            avvisati.clear()
            gol_memoria.clear()
            giorno_reset = now_it.day

        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")

        if live == "LIMIT":
            tg("Limite API pausa 1h")
            time.sleep(3600)
            continue

        if not live:
            time.sleep(60)
            continue

        # PALINSESTO GOL GOL OGNI 3 ORE
        if time.time() - ultimo_golgol >= 10800:
            oggi_str = now_it.strftime("%Y-%m-%d")
            fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi_str}")
            if fixtures and fixtures!= "LIMIT":
                buone = [f for f in fixtures if f["fixture"]["status"]["short"] == "NS" and not any(b in f["league"]["name"] for b in BLACK)]
                if buone:
                    txt = f"PALINSESTO GOL GOL - {now_it.strftime('%H:%M')}\n\n"
                    for ff in buone[:2]:
                        txt += f"{ff['teams']['home']['name']} vs {ff['teams']['away']['name']}\n{ff['league']['name']}\nGOL GOL SI\n\n"
                    tg(txt)
            ultimo_golgol = time.time()

        for g in live:
            fid = g["fixture"]["id"]
            m = g["fixture"]["status"]["elapsed"] or 0
            gh = g["goals"]["home"]
            ga = g["goals"]["away"]
            tot = gh + ga
            lega = g["league"]["name"]

            if any(b in lega for b in BLACK):
                continue

            if fid in avvisati and tot > gol_memoria.get(fid, 0):
                tg(f"GOL VINTO! {m} {lega} {g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}")

            gol_memoria[fid] = tot

            if m < 55 or m > 88:
                continue
            if fid in avvisati:
                continue
            if abs(gh - ga) >= 3:
                continue
            if gh + ga >= 5:
                continue

            perc = 80 + (5 if m >= 65 else 0) + (5 if m >= 75 else 0)
            p = min(perc, 92)
            tg(f"{m} >80% {lega} {g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']} Prob {p}%")
            avvisati.add(fid)

        time.sleep(60)

    except Exception as e:
        tg(f"ERRORE {e}")
        time.sleep(30)
