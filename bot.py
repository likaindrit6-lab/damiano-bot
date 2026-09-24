
import requests, time, threading
from datetime import datetime

# --- INSERISCI QUI I TUOI DATI ---
API_KEY = "LA_TUA_API_KEY_API_FOOTBALL"
TELEGRAM_TOKEN = "IL_TUO_TOKEN_TELEGRAM"
CHAT_ID = "IL_TUO_CHAT_ID"

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {"x-apisports-key": API_KEY}

# Memoria per non mandare doppioni
inviati = set()
inviati_gol = set()
inviati_schedina = set()

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print(f"INVIATO: {msg[:50]}")
    except Exception as e:
        print(f"Errore TG: {e}")

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

def get_stat(fixture_id):
    try:
        r = requests.get(f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}", headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except: return []

def get_team_avg_goals(team_id, last=5):
    try:
        r = requests.get(f"{BASE_URL}/fixtures?team={team_id}&last={last}", headers=HEADERS, timeout=20)
        res = r.json().get("response", [])
        if not res: return 0
        goals = 0
        for f in res:
            if f["teams"]["home"]["id"] == team_id:
                goals += f["goals"]["home"] or 0
            else:
                goals += f["goals"]["away"] or 0
        return goals / len(res)
    except: return 0

# --- 1. CORNER LIVE H24 - IL TUO CHE FUNZIONA ---
def loop_live():
    print("Loop LIVE partito H24")
    while True:
        try:
            for f in get_live():
                try:
                    fid = f["fixture"]["id"]
                    minute = f["fixture"]["status"]["elapsed"] or 0
                    if not (35 <= minute <= 65): continue

                    home = f["teams"]["home"]["name"]
                    away = f["teams"]["away"]["name"]

                    stats = get_stat(fid)
                    if not stats: continue

                    total_corners = 0
                    for team_stat in stats:
                        for s in team_stat.get("statistics", []):
                            if s["type"] == "Corner Kicks":
                                total_corners += s["value"] or 0

                    if total_corners >= 5:
                        key = f"{fid}_{total_corners}"
                        if key not in inviati:
                            msg = f"🚩 <b>CORNER LIVE {minute}'</b>\n{home} vs {away}\nCorner: {total_corners}\nNext: OVER 8.5 CORNER"
                            tg(msg)
                            inviati.add(key)
                except: continue
        except: pass
        time.sleep(60)

# --- 2. GOL GOL OGNI 2 ORE - CORRETTO SENZA DOPPIONI ---
def gol_gol_loop():
    print("Loop GOL GOL partito")
    while True:
        try:
            oggi = datetime.now().strftime("%Y-%m-%d")
            fixtures = get_fixtures_date(oggi)
            picks = []
            for f in fixtures:
                try:
                    if f["fixture"]["status"]["short"]!= "NS": continue
                    hid = f["teams"]["home"]["id"]
                    aid = f["teams"]["away"]["id"]
                    avg_h = get_team_avg_goals(hid)
                    avg_a = get_team_avg_goals(aid)
                    if avg_h >= 1.0 and avg_a >= 1.0:
                        picks.append((f["fixture"]["id"], f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"))
                    if len(picks) == 3: break
                except: continue

            if len(picks) == 3:
                key_gol = f"{oggi}_" + "_".join([str(p[0]) for p in picks])
                if key_gol not in inviati_gol:
                    msg = "⚽️ <b>GOL GOL - 3 partite</b>\n\n" + "\n".join([f"🥅 {p[1]} - Gol" for p in picks])
                    tg(msg)
                    inviati_gol.add(key_gol)
                    print(f"Gol Gol inviato: {key_gol}")
                else:
                    print(f"Gol Gol già inviato oggi, salto: {key_gol}")
        except Exception as e:
            print(f"Errore gol_gol_loop: {e}")
        time.sleep(7200) # 2 ore

# --- 3. SCHEDINA 10:00 ---
def schedina_facile_e_over():
    try:
        oggi = datetime.now().strftime("%Y-%m-%d")
        domani = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if oggi in inviati_schedina:
            print("Schedina già inviata oggi")
            return
        fixtures = get_fixtures_date(domani)
        # qui metti la tua logica schedina facile e over...
        # per ora ti mando un esempio
        msg = f"📋 <b>SCHEDINA DEL GIORNO {domani}</b>\n\nIn aggiornamento..."
        # tg(msg)
        inviati_schedina.add(oggi)
    except Exception as e:
        print(f"Errore schedina: {e}")

# --- AVVIO BOT ---
tg("✅ <b>BOT DAMI ACCESO</b>\nCorner H24 attivo\nGol Gol anti-doppione attivo")

threading.Thread(target=loop_live, daemon=True).start()
threading.Thread(target=gol_gol_loop, daemon=True).start()

print("Bot avviato correttamente")

while True:
    now = datetime.now()
    if now.hour == 10 and now.minute == 0:
        schedina_facile_e_over()
        time.sleep(61)
    time.sleep(30)
