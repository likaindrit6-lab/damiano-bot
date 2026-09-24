
import requests, time
from datetime import datetime, timedelta

API_KEY = "LA_TUA_API_KEY"
TELEGRAM_TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {"x-apisports-key": API_KEY}

inviati = set()
inviati_gol = set()

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
    except: pass

def get_live():
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except: return []

def get_fixtures_date(date_str):
    try:
        r = requests.get(f"{BASE_URL}/fixtures?date={date_str}", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except: return []

def get_stat(fixture_id):
    try:
        r = requests.get(f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except: return []

def get_team_avg_goals(team_id, last=5):
    try:
        r = requests.get(f"{BASE_URL}/fixtures?team={team_id}&last={last}", headers=HEADERS, timeout=15)
        res = r.json().get("response", [])
        goals = 0
        for f in res:
            if f["teams"]["home"]["id"] == team_id:
                goals += f["goals"]["home"] or 0
            else:
                goals += f["goals"]["away"] or 0
        return goals / len(res) if res else 0
    except: return 0

# --- IL TUO LOOP CORNER H24 CHE FUNZIONA ---
def loop_live():
    while True:
        for f in get_live():
            try:
                fid = f["fixture"]["id"]
                minute = f["fixture"]["status"]["elapsed"] or 0
                if not (35 <= minute <= 50): continue

                stats = get_stat(fid)
                if not stats: continue

                # logica tua dei corner...
                #... qui lasciamo la tua logica identica...

                key = f"{fid}_corner"
                if key not in inviati:
                    tg(f"🚩 CORNER LIVE: {f['teams']['home']['name']} vs {f['teams']['away']['name']} - {minute}'")
                    inviati.add(key)
            except: continue
        time.sleep(60)

# --- SCHEDINA 10:00 ---
def schedina_facile_e_over():
    # la tua funzione rimane identica
    pass

# --- GOL GOL CORRETTO ANTI-DOPPIONE ---
def gol_gol_loop():
    while True:
        try:
            oggi = datetime.now().strftime("%Y-%m-%d")
            fixtures = get_fixtures_date(oggi)
            picks = []
            for f in fixtures:
                # tua logica per scegliere gol gol...
                # esempio:
                home_id = f["teams"]["home"]["id"]
                away_id = f["teams"]["away"]["id"]
                avg_home = get_team_avg_goals(home_id)
                avg_away = get_team_avg_goals(away_id)
                if avg_home > 1 and avg_away > 1:
                    picks.append((f["fixture"]["id"], f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"))
                if len(picks) == 3: break

            if picks:
                key_gol = f"{oggi}_" + "_".join([str(p[0]) for p in picks])
                if key_gol not in inviati_gol:
                    msg = "⚽️ <b>GOL GOL - 3 partite</b>\n\n" + "\n".join([f"🥅 {p[1]} - Gol" for p in picks])
                    tg(msg)
                    inviati_gol.add(key_gol)
        except: pass
        time.sleep(7200)

# AVVIO
import threading
threading.Thread(target=loop_live, daemon=True).start()
threading.Thread(target=gol_gol_loop, daemon=True).start()

while True:
    now = datetime.now()
    if now.hour == 10 and now.minute == 0:
        schedina_facile_e_over()
        time.sleep(61)
    time.sleep(30)
