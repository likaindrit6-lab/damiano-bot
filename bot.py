import os, time, requests
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")
API = os.getenv("API_FOOTBALL_KEY")

def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT, "text": m, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

send("✅ V11 PARTITO - CODE FIXATO")

headers = {"x-apisports-key": API}

while True:
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures?live=all",
        headers=headers, timeout=20).json().get("response",[])

        for x in r:
            try:
                f = x["fixture"]
                g = x["goals"]
                mi = f["status"]["elapsed"] or 0
                if g["home"]!= 0 or g["away"]!= 0: continue
                if mi < 20 or mi > 85: continue

                fid = f["id"]
                home = x["teams"]["home"]["name"]
                away = x["teams"]["away"]["name"]

                s = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}",
                headers=headers, timeout=15).json().get("response",[])
                if len(s) < 2: continue

                def get_stat(arr, name):
                    for z in arr:
                        if name.lower() in z["type"].lower():
                            return z["value"] or 0
                    return 0

                hs = s[0]["statistics"]
                aw = s[1]["statistics"]
                tiri = get_stat(hs, "Shots on Goal") + get_stat(aw, "Shots on Goal")
                cor = get_stat(hs, "Corner") + get_stat(aw, "Corner")

                if 30 <= mi <= 55:
                    if tiri >= 4 and cor >= 4:
                        send(f"🔥 CALDA {mi}' {home}-{away} 0-0 T:{tiri} C:{cor}")
                    elif tiri <= 1 and cor <= 2:
                        send(f"❄️ FREDDA {mi}' {home}-{away} 0-0 T:{tiri} C:{cor}")
                time.sleep(1)
            except:
                continue
        time.sleep(60)
    except:
        time.sleep(30)
