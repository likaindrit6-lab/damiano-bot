
import os, requests, time
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL") or os.getenv("API_KEY") or os.getenv("FOOTBALL_API")

HEAD = {"x-apisports-key": API_KEY}
inviate = set()
last_gg = 0
last_quota = ""

def send(t):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=15)
    except: pass

def get_stats(fid):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=20).json()
        d = {"on":0, "corn":0, "red":0}
        for tm in r.get("response", []):
            for s in tm.get("statistics", []):
                v = s["value"]
                if v is None: continue
                if "Shots on Goal" in s["type"]: d["on"] += int(v)
                if "Corner" in s["type"]: d["corn"] += int(v)
                if "Red Cards" in s["type"] or "Red" in s["type"]: d["red"] += int(v)
        return d
    except: return None

def get_fixture_info(m):
    casa = m["teams"]["home"]["name"]
    fuori = m["teams"]["away"]["name"]
    league = m["league"]["name"]
    country = m["league"]["country"]
    fid = m["fixture"]["id"]
    elapsed = m["fixture"]["status"]["elapsed"] or 0
    return casa, fuori, league, country, fid, elapsed

def check_media_gol(team_id):
    # controlla ultime 5 partite se media gol >1.5
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEAD, timeout=20).json()
        tot = 0
        n = 0
        for f in r.get("response", []):
            tot += (f["goals"]["home"] or 0) + (f["goals"]["away"] or 0)
            n+=1
        return (tot/n) >= 1.5 if n>0 else False
    except: return False

print("BOT DAMI V7 - LIVE")

while True:
    try:
        # 1. LIVE CHECK
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json()
        for m in live.get("response", []):
            casa, fuori, league, country, fid, el = get_fixture_info(m)
            if el == 0: continue
            stats = get_stats(fid)
            if not stats: continue

            # 1. CALDA 5 tiri porta entro 50'
            key = f"calda-{fid}"
            if el <= 50 and stats["on"] >= 5 and key not in inviate:
                send(f"🔥 CALDA {el}' - 5 tiri in porta\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(key)

            # 2. CORNER 5 entro 45'
            key = f"corner-{fid}"
            if el <= 45 and stats["corn"] >= 5 and key not in inviate:
                send(f"🚩 CORNER 5 al {el}' - Corner primo tempo: {stats['corn']}\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(key)

            # 3. MORTA 3 tiri entro 60'
            key = f"morta-{fid}"
            if el >= 55 and el <= 65 and stats["on"] <= 3 and key not in inviate:
                send(f"🧊 MORTA {el}' - Solo {stats['on']} tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(key)

            # 4. ROSSO entro 60'
            key = f"rosso-{fid}"
            if el <= 60 and stats["red"] >= 1 and key not in inviate:
                send(f"🟥 ROSSO al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(key)

        # 5. SCHEDINA GOL GOL OGNI 2 ORE
        if time.time() - last_gg > 7200:
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                f = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=20).json()
                lista = []
                for match in f.get("response", [])[:20]:
                    h_id = match["teams"]["home"]["id"]
                    a_id = match["teams"]["away"]["id"]
                    if check_media_gol(h_id) and check_media_gol(a_id):
                        lista.append(f"{match['teams']['home']['name']} vs {match['teams']['away']['name']} - {match['league']['name']}")
                    if len(lista)>=3: break
                if lista:
                    txt = "⚽️ SCHEDINA GOL GOL - Over 1.5 media\n\n" + "\n".join([f"{i+1}. {x} -> GOL" for i,x in enumerate(lista[:3])])
                    send(txt)
                last_gg = time.time()
            except: pass

        # 6. SCHEDINA QUOTA BASSA ORE 10:00
        now = datetime.now()
        if now.hour == 10 and now.minute < 2 and last_quota != now.strftime("%Y-%m-%d"):
            send("💰 SCHEDINA QUOTA BASSA 1.60/1.70 - Ore 10:00\n\n1. City vs Luton - 1 (1.20)\n2. Inter vs Verona - 1 (1.25)\n3. Bayern vs Mainz - 1 (1.18)\n4. PSG vs Lorient - 1 (1.22)\nTotale ~1.68 - Quote sicure")
            last_quota = now.strftime("%Y-%m-%d")

        time.sleep(60)
    except Exception as e:
        print("err", e)
        time.sleep(60)
