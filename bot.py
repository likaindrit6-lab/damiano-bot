import os, time, requests, traceback
from datetime import datetime
import pytz

ROMA = pytz.timezone('Europe/Rome')
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

print("=== BOT DAMI V11 PARTITO ===")

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT, "text": msg, "parse_mode": "HTML"}, timeout=15)
    except: pass

send("✅ V11 PARTITO - Anti-crash ON")

headers = {"x-apisports-key": API_KEY}

while True:
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=20).json()
        lives = r.get("response", [])

        for m in lives:
            try:
                fixture = m["fixture"]
                goals = m["goals"]
                minuto = fixture["status"]["elapsed"] or 0
                if goals["home"]!=0 or goals["away"]!=0: continue
                if minuto < 20 or minuto > 85: continue

                fid = fixture["id"]
                home = m["teams"]["home"]["name"]
                away = m["teams"]["away"]["name"]

                s = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=headers, timeout=15).json()
                if not s.get("response"): continue
                if len(s["response"]) < 2: continue

                def get(arr, name):
                    for x in arr:
                        if name.lower() in x["type"].lower():
                            return x["value"] or 0
                    return 0

                hs = s["response"][0]["statistics"]
                aw = s["response"][1]["statistics"]
                tiri = get(hs, "Shots on Goal") + get(aw, "Shots on Goal")
                corner = get(hs, "Corner") + get(aw, "Corner")

                if minuto >= 30 and minuto <= 55:
                    if tiri >= 4 and corner >= 4:
                        send(f"🔥 CALDA {minuto}' {home}-{away} 0-0 Tiri:{tiri} Corner:{corner}")
                    elif tiri <= 1 and corner <= 2:
                        send(f"❄️ FREDDA {minuto}' {home}-{away} 0-0 Tiri:{tiri} Corner:{corner}")
                time.sleep(1)
            except: continue
        time.sleep(60)
    except:
        time.sleep(30)
