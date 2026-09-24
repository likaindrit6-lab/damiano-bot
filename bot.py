
import requests, time, threading
from datetime import datetime

API_KEY = "LA TUA KEY"
TELEGRAM_TOKEN = "IL TUO TOKEN"
CHAT_ID = "IL TUO CHAT ID"

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY, "x-rapidapi-host": "v3.football.api-sports.io"}

inviati = set()
inviato_gol_oggi = ""

def tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=20)
        print(f"Telegram: {r.text}", flush=True)
    except Exception as e:
        print(f"Errore: {e}", flush=True)

def loop_live():
    while True:
        try:
            r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS, timeout=20)
            for f in r.json().get("response", []):
                fid = f["fixture"]["id"]
                minute = f["fixture"]["status"]["elapsed"] or 0
                if 35 <= minute <= 75:
                    key = f"{fid}_{minute}"
                    if key not in inviati:
                        home = f["teams"]["home"]["name"]
                        away = f["teams"]["away"]["name"]
                        tg(f"🚩 CORNER {minute}'\n{home} vs {away}")
                        inviati.add(key)
        except: pass
        time.sleep(90)

def loop_gol():
    global inviato_gol_oggi
    while True:
        try:
            oggi = datetime.now().strftime("%Y-%m-%d")
            if inviato_gol_oggi != oggi:
                r = requests.get(f"{BASE_URL}/fixtures?date={oggi}", headers=HEADERS, timeout=20)
                picks = []
                for f in r.json().get("response", [])[:50]:
                    if f["fixture"]["status"]["short"] == "NS":
                        picks.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}")
                        if len(picks) == 3: break
                if len(picks) == 3:
                    msg = f"⚽️ GOL GOL {oggi}\n\n" + "\n".join([f"🥅 {p}" for p in picks])
                    tg(msg)
                    inviato_gol_oggi = oggi
        except: pass
        time.sleep(3600)

tg("✅ BOT DAMI ACCESO")
threading.Thread(target=loop_live, daemon=True).start()
threading.Thread(target=loop_gol, daemon=True).start()

while True: time.sleep(60)
