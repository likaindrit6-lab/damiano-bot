
import requests, time, threading
from datetime import datetime

API_KEY = "LA TUA KEY"
TELEGRAM_TOKEN = "IL TUO TOKEN"
CHAT_ID = "IL TUO CHAT ID"

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY, "x-rapidapi-host": "v3.football.api-sports.io"}

inviati_corner = set()
inviati_gol = set()

def tg(msg):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=20)

def get_live():
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except: return []

def get_today():
    try:
        oggi = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(f"{BASE_URL}/fixtures?date={oggi}", headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except: return []

def loop_corner():
    while True:
        for f in get_live():
            fid = f["fixture"]["id"]
            minute = f["fixture"]["status"]["elapsed"] or 0
            if 35 <= minute <= 70:
                key = f"{fid}_{minute}"
                if key not in inviati_corner:
                    home = f["teams"]["home"]["name"]
                    away = f["teams"]["away"]["name"]
                    tg(f"🚩 <b>CORNER {minute}'</b>\n{home} vs {away}")
                    inviati_corner.add(key)
        time.sleep(90)

def loop_gol():
    while True:
        fixtures = get_today()
        picks = []
        for f in fixtures:
            if f["fixture"]["status"]["short"] == "NS":
                picks.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}")
                if len(picks) == 3: break
        if len(picks) == 3:
            oggi = datetime.now().strftime("%Y-%m-%d")
            key_gol = f"{oggi}_{picks[0]}"
            if key_gol not in inviati_gol:
                msg = f"⚽️ <b>GOL GOL {oggi}</b>\n\n" + "\n".join([f"🥅 {p}" for p in picks])
                tg(msg)
                inviati_gol.add(key_gol)
        time.sleep(10800)

tg("✅ BOT DAMI ACCESO - pronto")
threading.Thread(target=loop_corner, daemon=True).start()
threading.Thread(target=loop_gol, daemon=True).start()
while True: time.sleep(60)
