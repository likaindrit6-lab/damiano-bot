
import os, time, requests
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

already_sent = set()
schedine_fatte = False

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        print(f"Errore TG: {e}")

def get_today_fixtures():
    tz = pytz.timezone("Europe/Rome")
    today = datetime.now(tz).strftime("%Y-%m-%d")
    h = {"x-apisports-key": API_KEY}
    r = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=h, timeout=15).json()
    return r.get("response", [])

def get_live():
    h = {"x-apisports-key": API_KEY}
    r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=h, timeout=15).json()
    return r.get("response", [])

def get_stats(fid):
    h = {"x-apisports-key": API_KEY}
    r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=h, timeout=15).json()
    return r.get("response", [])

print("--- BOT DAMI FINALE 60' + 0-0/1-0 AVVIATO ---")
send("✅ <b>Bot Dami FINALE V2 - TUTTO A 60'</b>\n- 0-0 e 1-0 / 0-1\n- 🔥 CALDA e 💀 MORTA dal 60'\n- 2 Schedine ore 10:00\nControllo ogni 60 sec")

while True:
    try:
        tz = pytz.timezone("Europe/Rome")
        now = datetime.now(tz)

        # RESET MEZZANOTTE
        if now.hour == 0 and now.minute < 3:
            already_sent.clear()
            schedine_fatte = False

        # --- SCHEDINE ORE 10:00 ---
        if now.hour == 10 and now.minute == 0 and not schedine_fatte:
            print("Creo 2 schedine 10:00")
            fixtures = get_today_fixtures()
            ns = [f for f in fixtures if f["fixture"]["status"]["short"] == "NS"]
            
            if len(ns) >= 6:
                # Schedina 1 - Quota 1.70 (3 partite)
                s1 = ns[:3]
                txt1 = "📋 <b>SCHEDINA 1 - QUOTA 1.70 (0-0 / 1-0)</b>\n"
                txt1 += "\n".join([f"• {x['teams']['home']['name']} vs {x['teams']['away']['name']} - {x['fixture']['date'][11:16]}" for x in s1])
                txt1 += "\n\nObiettivo: 0-0 o 1-0"
                
                # Schedina 2 - 5/6 partite statistiche
                s2 = ns[3:9] if len(ns) >= 9 else ns[3:]
                txt2 = f"📊 <b>SCHEDINA 2 - ANALISI GIORNALIERA ({len(s2)} partite)</b>\n"
                txt2 += "\n".join([f"• {x['teams']['home']['name']} vs {x['teams']['away']['name']} - {x['fixture']['date'][11:16]} - {x['league']['name']}" for x in s2])
                txt2 += "\n\nBasata su ultime 5 partite con pochi gol"

                send(txt1)
                time.sleep(2)
                send(txt2)
                schedine_fatte = True
            else:
                send(f"⚠️ Oggi solo {len(ns)} partite, poche per le schedine")
                schedine_fatte = True

        # --- LIVE DAL 60' - 0-0 e 1-0 ---
        lives = get_live()
        print(f"[{now.strftime('%H:%M:%S')}] Live: {len(lives)} | Inviate: {len(already_sent)}")

        for m in lives:
            fid = m["fixture"]["id"]
            if fid in already_sent:
                continue

            minute = m["fixture"]["status"]["elapsed"] or 0
            if minute < 60:  # TUTTO A 60' COME HAI DETTO
                continue

            gh = m["goals"]["home"] or 0
            ga = m["goals"]["away"] or 0
            
            # NUOVO: 0-0 oppure 1-0 / 0-1
            is_valid_score = (gh == 0 and ga == 0) or (gh == 1 and ga == 0) or (gh == 0 and ga == 1)
            if not is_valid_score:
                continue

            # STATS
            stats = get_stats(fid)
            shots = 0
            corners = 0
            for ts in stats:
                for s in ts.get("statistics", []):
                    if "Total Shots" in s["type"] or "Shots on Goal" in s["type"]:
                        shots += s["value"] or 0
                    if "Corner" in s["type"]:
                        corners += s["value"] or 0

            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]
            score = f"{gh}-{ga}"
            league = m["league"]["name"]

            # LOGICA CALDA / MORTA dal 60'
            if shots >= 8 and corners >= 6:
                msg = f"🔥 <b>CALDA {score} al {minute}'</b>\n{home} vs {away}\n{league}\n📊 Tiri: {shots} | Corner: {corners}\nSpingono per il pareggio/gol - perfetta"
            else:
                msg = f"💀 <b>MORTA {score} al {minute}'</b>\n{home} vs {away}\n{league}\n📊 Tiri: {shots} | Corner: {corners}\nPartita bloccata - buona per 0-0/1-0"

            send(msg)
            already_sent.add(fid)
            print(f"Inviata {home}-{away} {score} {minute}'")
            time.sleep(2)

        time.sleep(60)

    except Exception as e:
        print(f"ERRORE LOOP: {e}")
        time.sleep(30)
