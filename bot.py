
import os, requests, time, random
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL")
HEAD = {"x-apisports-key": API_KEY}

print("=== BOT DAMI AVVIO ===", flush=True)

try:
    requests.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)
except: pass

inviate = set()
ID = random.randint(1000,9999)

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=20)
    except Exception as e:
        print(f"Errore send {e}", flush=True)

def get_stats(fid):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=15).json()
        d = {"on":0,"corn":0,"red":0}
        for tm in r.get("response", []):
            for s in tm.get("statistics", []):
                if s["value"] is None: continue
                if "Shots on Goal" in s["type"]: d["on"]+=int(s["value"])
                if "Corner" in s["type"]: d["corn"]+=int(s["value"])
                if "Red" in s["type"]: d["red"]+=int(s["value"])
        return d
    except: return {"on":0,"corn":0,"red":0}

def get_today():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=15).json()
        return r.get("response", [])
    except: return []

send(f"✅ BOT DAMI {ID} PARTITO - CALDE/FREDDE ATTIVO")
ultimo_over_check = 0
ultimo_riepilogo = 0

while True:
    try:
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=15).json().get("response", [])
        
        calde_live = []
        fredde_count = 0

        for m in live:
            el = m["fixture"]["status"]["elapsed"] or 0
            if el < 2 or m["goals"]["home"]!=0 or m["goals"]["away"]!=0: continue
            fid = m["fixture"]["id"]
            casa = m["teams"]["home"]["name"]
            fuori = m["teams"]["away"]["name"]
            league = m["league"]["name"]
            country = m["league"]["country"]
            stats = get_stats(fid)
            time.sleep(0.6)

            # --- ALERT SINGOLI ---
            if 30 <= el <= 45 and stats["on"] >= 4 and f"calda-{fid}" not in inviate:
                send(f"🔥 CALDA {el}' - 4+ tiri in porta\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"calda-{fid}")
            if 25 <= el <= 45 and stats["corn"] >= 4 and f"corn-{fid}" not in inviate:
                send(f"🚩 CORNER 4 al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"corn-{fid}")
            if 30 <= el <= 45 and stats["on"] <= 2 and f"morta-{fid}" not in inviate:
                send(f"🧊 MORTA {el}' - {stats['on']} tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"morta-{fid}")
            if el <= 60 and stats["red"] >= 1 and f"rosso-{fid}" not in inviate:
                send(f"🟥 ROSSO al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"rosso-{fid}")

            # --- CONTEGGIO PER RIEPILOGO ---
            if 20 <= el <= 55:
                if stats["on"] >= 3 or stats["corn"] >= 4:
                    calde_live.append(f"🔥 {casa} vs {fuori} {el}' - C{stats['corn']} T{stats['on']}")
                elif stats["on"] <= 2:
                    fredde_count += 1

        # RIEPILOGO OGNI 10 MIN = 600 sec
        if time.time() - ultimo_riepilogo > 600:
            ultimo_riepilogo = time.time()
            tot_check = len([x for x in live if 20 <= (x["fixture"]["status"]["elapsed"] or 0) <= 55])
            if tot_check > 0:
                if calde_live:
                    send(f"⚽ LIVE ORA: 🔥 {len(calde_live)} CALDE / 🥶 {fredde_count} FREDDE\n\n" + "\n".join(calde_live[:7]))
                else:
                    send(f"🥶 FREDDA - {tot_check} live al 20-55', 0 calde / {fredde_count} fredde")

        # SCHEDINE 10:00 + OVER + GOL GOL 40% OGNI 2H
        now = datetime.now()
        if now.hour == 10 and now.minute < 5:
            key = f"quota-{now.strftime('%Y-%m-%d')}"
            if key not in inviate:
                tod = get_today()
                if len(tod) >= 3:
                    txt = "💰 SCHEDINA 10:00 - Quota 1.60/1.70\n\n"
                    for i,f in enumerate(tod[:3],1):
                        txt+=f"{i}. {f['teams']['home']['name']} vs {f['teams']['away']['name']} - 1X\n 🏆 {f['league']['name']} - {f['league']['country']}\n"
                    txt+="\nQuota finale: ~1.70"
                    send(txt)
                    inviate.add(key)
            key2 = f"over-media-{now.strftime('%Y-%m-%d')}"
            if key2 not in inviate:
                tod = get_today()
                over_list=[]
                for f in tod:
                    if f["fixture"]["status"]["short"]!="NS": continue
                    try:
                        time.sleep(0.7)
                        r1 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={f['teams']['home']['id']}&last=5", headers=HEAD, timeout=15).json()
                        tot1=sum([x["goals"]["home"]+
