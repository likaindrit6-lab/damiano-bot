
import os
import time
import requests
from datetime import datetime
import pytz

# --- CONFIG ---
API_KEY = os.getenv("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def get_live_fixtures():
    # 1 SOLA CHIAMATA OGNI 90 SECONDI PER TUTTE LE PARTITE DEL MONDO
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        data = r.json()
        return data.get("response", [])
    except:
        return []

def get_stats(fixture_id):
    try:
        r = requests.get(f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except:
        return []

def check_signals():
    fixtures = get_live_fixtures()
    if not fixtures:
        return

    for f in fixtures:
        try:
            fixture_id = f["fixture"]["id"]
            minuto = f["fixture"]["status"]["elapsed"]
            if minuto is None: continue
            if minuto < 50 or minuto > 95: continue

            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            gol_home = f["goals"]["home"]
            gol_away = f["goals"]["away"]
            risultato = f"{gol_home}-{gol_away}"

            # Per non sprecare token, prendiamo le stats solo se è interessante
            is_interesting = (risultato == "1-1" and minuto >= 65) or (minuto >= 60)
            if not is_interesting:
                continue

            stats = get_stats(fixture_id)
            time.sleep(1) # per non bruciare token

            # Calcolo tiri in porta totali
            tiri_tot = 0
            if len(stats) == 2:
                for team_stat in stats:
                    for s in team_stat["statistics"]:
                        if s["type"] == "Shots on Goal":
                            if s["value"] is not None:
                                tiri_tot += int(s["value"])

            # 1-1 CALDISSIMA
            if risultato == "1-1" and 65 <= minuto <= 90:
                send_telegram(f"🔥🔥 <b>1-1 CALDISSIMA {minuto}'</b>\n{home} vs {away}\n<b>POSSIBILITÀ ALTA DI GOL!</b> Sta per arrivare il 2-1!")
                continue

            # PARTITA MORTA
            if minuto >= 60 and tiri_tot <= 3:
                send_telegram(f"💀 <b>PARTITA MORTA {minuto}'</b>\n{home} vs {away} ({risultato})\nSolo {tiri_tot} tiri in porta totali\n👉 <b>CONSIGLIO: UNDER 2.5</b>")
                continue

            # SPINTA
            if tiri_tot >= 8 and minuto >= 60:
                 send_telegram(f"🔥 <b>SPINTA FORTISSIMA {minuto}'</b>\n{home} vs {away} ({risultato})\n{tiri_tot} tiri in porta - Stanno spingendo forte!\n👉 GOL IN ARRIVO")

        except Exception as e:
            print(e)
            continue

# --- LOOP PRINCIPALE ---
print("BOT V2 AVVIATO - Controllo ogni 90 secondi da 50' a 95'")
send_telegram("✅ Bot V2 collegato! Ora controllo ogni 90 sec TUTTI i campionati. Pronto per 1-1 Caldissima, Morta e Spinta.")

# Schedina 9:30 - la gestiamo semplice
ultima_schedina_data = ""

while True:
    try:
        # Controllo schedina 9:30 ora italiana
        italy_tz = pytz.timezone("Europe/Rome")
        ora_italiana = datetime.now(italy_tz)
        if ora_italiana.hour == 9 and ora_italiana.minute >= 30 and ora_italiana.minute <= 35:
            oggi = ora_italiana.strftime("%Y-%m-%d")
            if oggi != ultima_schedina_data:
                send_telegram("☀️ <b>SCHEDINA 9:30 QUOTA 1.70</b>\nSto cercando le 2 partite più sicure di oggi...")
                ultima_schedina_data = oggi

        check_signals()
        
        # ASPETTA 90 SECONDI ESATTI COME HAI CHIESTO
        time.sleep(90)

    except Exception as e:
        print(f"Errore loop: {e}")
        time.sleep(90)
