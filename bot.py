
import os, time, requests, json
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

SENT_FILE = "sent.json"

def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_sent(s):
    try:
        with open(SENT_FILE, "w") as f:
            json.dump(list(s), f)
    except:
        pass

already_sent = load_sent()
schedine_fatte = False

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        print(f"Errore TG: {e}")

def get_live():
    h = {"x-apisports-key": API_KEY}
    r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=h, timeout=20).json()
    return r.get("response", [])

def get_stats(fid):
    h = {"x-apisports-key": API_KEY}
    r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=h, timeout=15).json()
    return r.get("response", [])

print("--- BOT V3 FIX SPAM AVVIATO ---")
# Manda messaggio avvio solo 1 volta al giorno
tz = pytz.timezone("Europe/Rome")
now = datetime.now(tz)
if now.hour == 13 and now.minute in [43,44]:
    send("✅ <b>Bot V3 FIX - Tutto a 60' - FIXATO</b>\n- No più spam\n- No U19 senza stats\n- 0-0 e 1-0 / 0-1")

while True:
    try:
        tz = pytz.timezone("Europe/Rome")
        now = datetime.now(tz)

        if now.hour == 0 and now.minute < 2:
            already_sent.clear()
            save_sent(already_sent)
            schedine_fatte = False

        lives = get_live()
        print(f"[{now.strftime('%H:%M:%S')}] Live: {len(lives)}")

        for m in lives:
            fid = m["fixture"]["id"]
            if fid in already_sent:
                continue

            minute = m["fixture"]["status"]["elapsed"] or 0
            if minute < 60:
                continue

            league_name = m["league"]["name"]
            # FILTRO LEGHE SCARSE
            if "U19" in league_name or "U18" in league_name or "U21" in league_name or "Reserve" in league_name or "Friendly" in league_name:
                continue

            gh = m["goals"]["home"] or 0
            ga = m["goals"]["away"] or 0
            if not ((gh==0 and ga==0) or (gh==1 and ga==0) or (gh==0 and ga==1)):
                continue

            stats = get_stats(fid)
            shots = 0
            corners = 0
            for ts in stats:
                for s in ts.get("statistics", []):
                    t = s.get("type","")
                    v = s.get("value") or 0
                    if t in ["Total Shots", "Shots on Goal", "Shots off Goal", "Blocked Shots"]:
                        shots += v
                    if "Corner" in t:
                        corners += v

            # SE NON HA STATS (tipo U19) NON LA MANDIAMO
            if shots == 0 and corners == 0:
                print(f"Skip {fid} no stats")
                continue

            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]
            score = f"{gh}-{ga}"

            if shots >= 8 and corners >= 6:
                msg = f"🔥 <b>CALDA {score} al {minute}'</b>\n{home} vs {away}\n{league_name}\n📊 Tiri: {shots} | Corner: {corners}"
            else:
                msg = f"💀 <b>MORTA {score} al {minute}'</b>\n{home} vs {away}\n{league_name}\n📊 Tiri: {shots} | Corner: {corners}\nBloccata - buona per 0-0/1-0"

            send(msg)
            already_sent.add(fid)
            save_sent(already_sent)
            print(f"Inviata {home} vs {away}")
            time.sleep(2)

        time.sleep(60)
    except Exception as e:
        print(f"ERRORE: {e}")
        time.sleep(30)
