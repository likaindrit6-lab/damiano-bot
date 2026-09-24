
import os, requests, time
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL") or os.getenv("API_KEY") or os.getenv("FOOTBALL_API")
HEAD = {"x-apisports-key": API_KEY}

inviate = set()
last_gg = 0
last_quota = ""
last_lista_gol = 0

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=30)
    except: pass

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
    except: return {"on":0,"corn":0,"red":0}

def get_today():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=20).json()
        return r.get("response", [])
    except: return []

def check_over15_last5(team_id):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEAD, timeout=20).json()
        games = r.get("response", [])
        if len(games) < 5: return False
        for g in games:
            if (g["goals"]["home"] or 0) + (g["goals"]["away"] or 0) <= 1: return False
        return True
    except: return False

def media_gol_fatti_last5(team_id):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEAD, timeout=20).json()
        games = r.get("response", [])
        if len(games) < 5: return 0
        tot = 0
        for g in games:
            if g["teams"]["home"]["id"] == team_id: tot += g["goals"]["home"] or 0
            else: tot += g["goals"]["away"] or 0
        return tot / 5.0
    except: return 0

send("✅ BOT DAMI COMPLETO - Tutto dentro")

while True:
    try:
        # LIVE 0-0
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json().get("response", [])
        for m in live:
            el = m["fixture"]["status"]["elapsed"] or 0
            if el < 1 or m["goals"]["home"]!= 0 or m["goals"]["away"]!= 0: continue
            fid = m["fixture"]["id"]
            casa = m["teams"]["home"]["name"]
            fuori = m["teams"]["away"]["name"]
            league = m["league"]["name"]
            country = m["league"]["country"]
            stats = get_stats(fid)
            if el <= 50 and stats["on"] >= 5 and f"calda-{fid}" not in inviate:
                send(f"🔥 CALDA {el}' - 5 tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"calda-{fid}")
            if el <= 45 and stats["corn"] >= 5 and f"corn-{fid}" not in inviate:
                send(f"🚩 CORNER 5 al {el}' - Tot {stats['corn']}\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"corn-{fid}")
            if 55 <= el <= 65 and stats["on"] <= 3 and f"morta-{fid}" not in inviate:
                send(f"🧊 MORTA {el}' - {stats['on']} tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"morta-{fid}")
            if el <= 60 and stats["red"] >= 1 and f"rosso-{fid}" not in inviate:
                send(f"🟥 ROSSO al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"rosso-{fid}")

        # GOL GOL OGNI 2 ORE
        if time.time() - last_gg > 7200:
            tod = get_today()
            buone = []
            for f in tod:
                if len(buone) >= 3: break
                if f["fixture"]["status"]["short"]!= "NS": continue
                if check_over15_last5(f["teams"]["home"]["id"]) and check_over15_last5(f["teams"]["away"]["id"]):
                    buone.append(f)
                time.sleep(0.3)
            if len(buone) >= 3:
                txt = "⚽️ SCHEDINA GOL GOL - Over 1.5 ultime 5\n\n"
                for i, b in enumerate(buone, 1):
                    txt += f"{i}. {b['teams']['home']['name']} vs {b['teams']['away']['name']} - GOL\n 🏆 {b['league']['name']} - {b['league']['country']}\n"
                send(txt)
            last_gg = time.time()

        # LISTA MEDIA GOL >1.5 CHE MI HAI CHIESTO ORA
        if time.time() - last_lista_gol > 7200:
            tod = get_today()
            lista = []
            for f in tod:
                if f["fixture"]["status"]["short"]!= "NS": continue
                for k in ["home","away"]:
                    team = f["teams"][k]
                    if any(x["id"] == team["id"] for x in lista): continue
                    media = media_gol_fatti_last5(team["id"])
                    if media > 1.5:
                        lista.append({"id":team["id"],"name":team["name"],"media":media,"league":f["league"]["name"],"country":f["league"]["country"],"vs":f['teams']['away']['name'] if k=='home' else f['teams']['home']['name']})
                time.sleep(0.4)
                if len(lista) >= 15: break
            if lista:
                txt = f"🔥 SQUADRE CALDE OGGI - Media >1.5 gol\n\n"
                for i, s in enumerate(lista, 1):
                    txt += f"{i}. {s['name']} - {s['media']:.1f} gol/5\n vs {s['vs']} - 🏆 {s['league']} - {s['country']}\n"
                send(txt[:4000])
            last_lista_gol = time.time()

        # QUOTA BASSA 10:00
        now = datetime.now()
        if now.hour == 10 and now.minute < 5 and last_quota!= now.strftime("%Y-%m-%d"):
            tod = get_today()
            if len(tod) >= 4:
                txt = "💰 SCHEDINA 10:00 - 1.60/1.70\n\n"
                for i, f in enumerate(tod[:4], 1):
                    txt += f"{i}. {f['teams']['home']['name']} vs {f['teams']['away']['name']} - 1X\n 🏆 {f['league']['name']} - {f['league']['country']}\n"
                send(txt)
                last_quota = now.strftime("%Y-%m-%d")

        time.sleep(60)
    except: time.sleep(60)
