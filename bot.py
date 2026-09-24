
import os, time, requests, traceback
from datetime import datetime
import pytz

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")
ROMA = pytz.timezone('Europe/Rome')

def log(msg):
    print(f"[{datetime.now(ROMA).strftime('%H:%M:%S')}] {msg}")

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        log(f"Errore invio TG: {e}")

log("=== BOT DAMI V10 COMPLETO AVVIATO ===")
send("✅ <b>BOT DAMI V10 COMPLETO PARTITO</b>\nOra controllo ogni 60 sec - Anti-crash ON")

headers = {"x-apisports-key": API_KEY}

while True:
    try:
        # 1. Prendo live
        r = requests.get("https://v3.football.api-sports.io/fixtures?live=all",
                         headers=headers, timeout=20)
        data = r.json()
        lives = data.get("response", [])
        log(f"Live trovate: {len(lives)}")

        if len(lives) == 0:
            time.sleep(60)
            continue

        for match in lives:
            try:
                fixture = match["fixture"]
                goals = match["goals"]
                minuto = fixture["status"]["elapsed"] or 0
                if goals["home"]!= 0 or goals["away"]!= 0: continue
                if minuto < 20 or minuto > 85: continue

                fixture_id = fixture["id"]
                home = match["teams"]["home"]["name"]
                away = match["teams"]["away"]["name"]

                # 2. Stats
                s = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}",
                                 headers=headers, timeout=15).json()

                if not s.get("response"): continue

                # Somma tiri, corner, attacchi pericolosi
                home_stats = s["response"][0]["statistics"]
                away_stats = s["response"][1]["statistics"]

                def get_stat(arr, nome):
                    for x in arr:
                        if nome in x["type"]:
                            return x["value"] or 0
                    return 0

                tiri_home = get_stat(home_stats, "Shots on Goal")
                tiri_away = get_stat(away_stats, "Shots on Goal")
                tiri = tiri_home + tiri_away

                corner_home = get_stat(home_stats, "Corner")
                corner_away = get_stat(away_stats, "Corner")
                corner = corner_home + corner_away

                # LOGICA TUA
                if minuto >= 30 and minuto <= 55:
                    if tiri >= 4 and corner >= 4:
                        send(f"🔥 <b>CALDA {minuto}'</b>\n{home} - {away}\nTiri: {tiri} | Corner: {corner}\nAncora 0-0")
                    elif tiri <= 1 and corner <= 2:
                        send(f"❄️ <b>FREDDA {minuto}'</b>\n{home} - {away}\nTiri: {tiri} | Corner: {corner} - Morta")

                time.sleep(1) # per non bruciare API

            except Exception as e:
                log(f"Errore su singola partita: {e}")
                continue

        log("Giro finito, aspetto 60 sec")
        time.sleep(60)

    except Exception as e:
        log(f"⚠️ ERRORE GLOBALE MA NON MI SPENGO:\n{traceback.format_exc()}")
        send(f"⚠️ Errore globale ma continuo a girare:\n{e}")
        time.sleep(30)
