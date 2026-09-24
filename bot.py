
import os, requests, time

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL") or os.getenv("API_KEY") or os.getenv("FOOTBALL_API")
HEAD = {"x-apisports-key": API_KEY}

inviate = set()

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=15)
    except: pass

print("BOT DAMI ON")
send("✅ BOT ACCESO - Dami, sono vivo, lista tua dentro")

def get_stats(fid):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=20).json()
        d = {"on":0, "corn":0, "red":0}
        for tm in r.get("response", []):
            for s in tm.get("statistics", []):
                if s["value"] is None: continue
                if "Shots on Goal" in s["type"]: d["on"] += int(s["value"])
                if "Corner" in s["type"]: d["corn"] += int(s["value"])
                if "Red" in s["type"]: d["red"] += int(s["value"])
        return d
    except:
        return {"on":0,"corn":0,"red":0}

while True:
    try:
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json().get("response", [])
        for m in live:
            el = m["fixture"]["status"]["elapsed"] or 0
            if el == 0: continue
            fid = m["fixture"]["id"]
            casa = m["teams"]["home"]["name"]
            fuori = m["teams"]["away"]["name"]
            league = m["league"]["name"]
            country = m["league"]["country"]
            stats = get_stats(fid)

            # 1. CALDA 5 tiri entro 50'
            if el <= 50 and stats["on"] >= 5 and f"calda-{fid}" not in inviate:
                send(f"🔥 CALDA {el}' - 5 tiri in porta\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"calda-{fid}")

            # 2. CORNER 5 entro 45'
            if el <= 45 and stats["corn"] >= 5 and f"corn-{fid}" not in inviate:
                send(f"🚩 CORNER 5 al {el}' - {stats['corn']} totali\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"corn-{fid}")

            # 3. MORTA 3 tiri entro 60'
            if 55 <= el <= 65 and stats["on"] <= 3 and f"morta-{fid}" not in inviate:
                send(f"🧊 MORTA {el}' - Solo {stats['on']} tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"morta-{fid}")

            # 4. ROSSO entro 60'
            if el <= 60 and stats["red"] >= 1 and f"rosso-{fid}" not in inviate:
                send(f"🟥 ROSSO al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"rosso-{fid}")

        time.sleep(60)
    except:
        time.sleep(60)
