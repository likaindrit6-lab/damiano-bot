
import requests, time, threading
from datetime import datetime, timedelta

# --- METTI QUI I TUOI 3 DATI ---
API_KEY = "LA TUA KEY API-FOOTBALL"
TELEGRAM_TOKEN = "IL TUO TOKEN TELEGRAM"
CHAT_ID = "IL TUO CHAT_ID"

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {"x-apisports-key": API_KEY}

# --- ECCO IL CASSETTINO DI MEMORIA, L'HO MESSO IO QUI ---
inviati = set()
inviati_gol = set() # <--- QUESTO E' QUELLO PER NON MANDARE 4 VOLTE GOIANESIA
inviati_schedina = set()

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print("INVIATO")
    except Exception as e:
        print(e)

def get_live():
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except: return []

def get_fixtures_date(date_str):
    try:
        r = requests.get(f"{BASE_URL}/fixtures?date={date_str}", headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except: return []

def get_stat(fid):
    try:
        r = requests.get(f"{BASE_URL}/fixtures/statistics?fixture={fid}", headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except: return []

def get_team_avg_goals(team_id):
    try:
        r = requests.get(f"{BASE_URL}/fixtures?team={team_id}&last=5", headers=HEADERS, timeout=20)
        res = r.json().get("response", [])
        if not res: return 0
        g=0
        for f in res:
            if f["teams"]["home"]["id"]==team_id: g+=f["goals"]["home"] or 0
            else: g+=f["goals"]["away"] or 0
        return g/len(res)
    except: return 0

def loop_live():
    print("LIVE H24 PARTITO")
    while True:
        try:
            for f in get_live():
                fid=f["fixture"]["id"]
                minute=f["fixture"]["status"]["elapsed"] or 0
                if not (35 <= minute <= 65): continue
                home=f["teams"]["home"]["name"]
                away=f["teams"]["away"]["name"]
                stats=get_stat(fid)
                tot=0
                for ts in stats:
                    for s in ts.get("statistics",[]):
                        if s["type"]=="Corner Kicks": tot+=s["value"] or 0
                if tot>=5:
                    key=f"{fid}_{tot}"
                    if key not in inviati:
                        tg(f"🚩 CORNER {minute}'\n{home} vs {away}\nCorner: {tot}")
                        inviati.add(key)
        except: pass
        time.sleep(60)

def gol_gol_loop():
    print("GOL GOL PARTITO")
    while True:
        try:
            oggi=datetime.now().strftime("%Y-%m-%d")
            fixtures=get_fixtures_date(oggi)
            picks=[]
            for f in fixtures:
                if f["fixture"]["status"]["short"]!="NS": continue
                hid=f["teams"]["home"]["id"]
                aid=f["teams"]["away"]["id"]
                if get_team_avg_goals(hid)>=1.0 and get_team_avg_goals(aid)>=1.0:
                    picks.append((f["fixture"]["id"], f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"))
                if len(picks)==3: break

            if len(picks)==3:
                key_gol = f"{oggi}_"+"_".join([str(p[0]) for p in picks])
                # --- QUI CONTROLLA IL CASSETTINO ---
                if key_gol not in inviati_gol:
                    msg = "⚽️ GOL GOL\n\n" + "\n".join([f"🥅 {p[1]} - Gol" for p in picks])
                    tg(msg)
                    inviati_gol.add(key_gol) # <--- E QUI SE LO RICORDA
                    print(f"Inviato gol gol: {key_gol}")
                else:
                    print(f"Gia inviato oggi, non lo rimando: {key_gol}")
        except Exception as e: print(e)
        time.sleep(7200)

# AVVIO
tg("✅ BOT DAMI ACCESO - tutto ok")
threading.Thread(target=loop_live, daemon=True).start()
threading.Thread(target=gol_gol_loop, daemon=True).start()

while True: time.sleep(30)
