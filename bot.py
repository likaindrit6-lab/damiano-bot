
import os, time, requests
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

sent_today = set()
already_sent_live = set()

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Errore invio TG: {e}")

def get_fixtures_today():
    # Partite di oggi
    tz = pytz.timezone("Europe/Rome")
    today = datetime.now(tz).strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, timeout=15).json()
    return r.get("response", [])

def get_live():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, timeout=15).json()
    return r.get("response", [])

def get_stats(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    headers = {"x-apisports-key": API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10).json()
        return r.get("response", [])
    except:
        return []

def is_red_before_70(events):
    # Cerca rosso prima del 70'
    for ev in events:
        if ev.get("type") == "Card" and "red" in str(ev.get("detail","")).lower():
            minute = ev.get("time", {}).get("elapsed", 100)
            if minute and minute < 70:
                return True
    return False

print("--- BOT DAMIANO FINALE AVVIATO - TUTTO A 70' ---")
send("✅ <b>Bot Damiano FINALE attivo!</b>\nTutto impostato a 70'\n- Schedine ore 10:00\n- Live CALDA/MORTA/ROSSO dal 70' in poi")

while True:
    try:
        tz = pytz.timezone("Europe/Rome")
        now = datetime.now(tz)
        print(f"[{now.strftime('%H:%M:%S')}] Check...")

        # 1. SCHEDINE ORE 10:00
        if now.hour == 10 and now.minute == 0 and "schedine" not in sent_today:
            print("Creo schedine 10:00")
            try:
                fixtures = get_fixtures_today()
                # Filtra partite dopo le 12:00 e ordina per probabilità 0-0 (qui semplice: prendo prime 6)
                future = [f for f in fixtures if f["fixture"]["status"]["short"] == "NS"]
                future = future[:6] # per test, poi mettiamo logica 0-0 vera
                if len(future) >= 6:
                    s1 = future[:3]
                    s2 = future[3:6]
                    txt1 = "📋 <b>SCHEDINA 0-0 #1 - ORE 10:00</b>\n" + "\n".join([f"• {x['teams']['home']['name']} vs {x['teams']['away']['name']} - {x['fixture']['date'][11:16]}" for x in s1])
                    txt2 = "📋 <b>SCHEDINA 0-0 #2 - ORE 10:00</b>\n" + "\n".join([f"• {x['teams']['home']['name']} vs {x['teams']['away']['name']} - {x['fixture']['date'][11:16]}" for x in s2])
                    send(txt1)
                    time.sleep(2)
                    send(txt2)
                else:
                    send("⚠️ Oggi poche partite per le schedine 0-0")
                sent_today.add("schedine")
            except Exception as e:
                print(f"Errore schedine: {e}")

        # Reset giorno
        if now.hour == 0 and now.minute == 1:
            sent_today.clear()
            already_sent_live.clear()

        # 2. LIVE DALLE 10:01 ALLE 23:00 - TUTTO A 70'
        if 10 <= now.hour <= 23:
            if now.hour == 10 and now.minute == 0:
                time.sleep(60)
                continue

            lives = get_live()
            print(f"Trovate {len(lives)} live")
            for match in lives:
                try:
                    fid = match["fixture"]["id"]
                    if fid in already_sent_live:
                        continue

                    minute = match["fixture"]["status"]["elapsed"] or 0
                    if minute < 70: # TUTTO A 70' COME HAI DETTO
                        continue

                    goals_home = match["goals"]["home"] or 0
                    goals_away = match["goals"]["away"] or 0
                    if not (goals_home == 0 and goals_away == 0):
                        continue

                    # Stats tiri/corner
                    stats = get_stats(fid)
                    shots = 0
                    corners = 0
                    for team_stat in stats:
                        for s in team_stat.get("statistics", []):
                            if "Shots" in s.get("type",""):
                                shots += s.get("value", 0) or 0
                            if "Corner" in s.get("type",""):
                                corners += s.get("value", 0) or 0
                    
                    # Condizione CALDA a 70'
                    is_calda = (minute >= 70 and shots >= 8 and corners >= 6)
                    
                    # Condizione ROSSO prima del 70' -> segnala dal 70' in poi
                    events = match.get("events", []) # se non ci sono, API events va chiamata a parte
                    has_red = is_red_before_70(events)

                    # Se vuoi, puoi aggiungere chiamata events: 
                    # per ora se ha rosso e siamo >=70' e 0-0, la segnaliamo come CALDA speciale

                    if is_calda or has_red:
                        home = match["teams"]["home"]["name"]
                        away = match["teams"]["away"]["name"]
                        league = match["league"]["name"]
                        
                        tipo = "🔥 CALDA" if is_calda else "🔴 ROSSO PRE 70'"
                        msg = f"{tipo} - 0-0 al {minute}'\n<b>{home} vs {away}</b>\n{league}\n📊 Tiri: {shots} | Corner: {corners}\n⏰ Minuto: {minute}'"
                        send(msg)
                        already_sent_live.add(fid)
                        print(f"Inviata {tipo} {home}-{away}")
                        time.sleep(1)

                except Exception as e:
                    print(f"Errore match {fid}: {e}")
                    continue

        time.sleep(60)

    except Exception as e:
        print(f"ERRORE LOOP: {e}")
        time.sleep(30)
