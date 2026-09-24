
import os, requests, time, random
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL")
HEAD = {"x-apisports-key": API_KEY}

print("=== BOT DAMI AVVIO ===", flush=True)
print(f"TOKEN ok:{bool(TOKEN)} CHAT:{CHAT_ID} API ok:{bool(API_KEY)}", flush=True)

try:
    requests.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)
    print("Webhook off", flush=True)
except Exception as e:
    print(f"Errore webhook {e}", flush=True)

inviate = set()
ID = random.randint(1000,9999)

def send(t):
    try:
        print(f"SEND TG: {t[:80]}", flush=True)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=20)
    except Exception as e:
        print(f"Errore send TG: {e}", flush=True)

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
    except Exception as e:
        print(f"Errore stats {fid}: {e}", flush=True)
        return {"on":0,"corn":0,"red":0}

def get_today():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=15).json()
        return r.get("response", [])
    except Exception as e:
        print(f"Errore today: {e}", flush=True)
        return []

send(f"✅ BOT DAMI {ID} PARTITO - Chiavi OK - Ora gira")
print(f"BOT {ID} PARTITO OK", flush=True)

ultimo_over_check = 0

while True:
    try:
        print("Check live...", flush=True)
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=15).json().get("response", [])
        print(f"Live trovate: {len(live)}", flush=True)

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

            # --- MODIFICHE DAMI SOLO QUI ---
            if 30 <= el <= 45 and stats["on"] >= 4 and f"calda-{fid}" not in inviate:
                send(f"🔥 CALDA {el}' - 4+ tiri in porta\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"calda-{fid}")
            if 25 <= el <= 45 and stats["corn"] >= 4 and f"corn-{fid}" not in inviate:
                send(f"🚩 CORNER 4 al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"corn-{fid}")
            if 30 <= el <= 45 and stats["on"] <= 2 and f"morta-{fid}" not in inviate:
                send(f"🧊 MORTA {el}' - {stats['on']} tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"morta-{fid}")
            # ROSSO IDENTICO
            if el <= 60 and stats["red"] >= 1 and f"rosso-{fid}" not in inviate:
                send(f"🟥 ROSSO al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"rosso-{fid}")

        # SCHEDINA 10:00 - QUOTA 1.60/1.70
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
            # SECONDA SCHEDINA 10:00 - OVER MEDIA >=2.0
            key2 = f"over-media-{now.strftime('%Y-%m-%d')}"
            if key2 not in inviate:
                tod = get_today()
                over_list=[]
                for f in tod:
                    if f["fixture"]["status"]["short"]!="NS": continue
                    try:
                        time.sleep(0.7)
                        r1 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={f['teams']['home']['id']}&last=5", headers=HEAD, timeout=15).json()
                        tot1=sum([x["goals"]["home"]+x["goals"]["away"] for x in r1.get("response",[])])
                        time.sleep(0.7)
                        r2 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={f['teams']['away']['id']}&last=5", headers=HEAD, timeout=15).json()
                        tot2=sum([x["goals"]["home"]+x["goals"]["away"] for x in r2.get("response",[])])
                        media=(tot1+tot2)/10
                        if media>=2.0:
                            over_list.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} - media {media:.2f}\n 🏆 {f['league']['name']} - {f['league']['country']}")
                    except: continue
                if over_list:
                    send("📊 SCHEDINA OVER 1.5 - Media >=2.0 ultime 5\n\n" + "\n\n".join(over_list[:8]))
                inviate.add(key2)

        # LISTA GOL GOL ogni 2 ore (7200 sec)
        if time.time() - ultimo_over_check > 7200:
            print("Check lista GOL GOL 2H...", flush=True)
            ultimo_over_check = time.time()
            tod = get_today()
            lista=[]
            for f in tod[:15]:
                if f["fixture"]["status"]["short"]!="NS": continue
                try:
                    time.sleep(0.8)
                    r1 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={f['teams']['home']['id']}&last=5", headers=HEAD, timeout=15).json()
                    gg1=0; tot1=0
                    for x in r1.get("response",[]):
                        gh=x["goals"]["home"]; ga=x["goals"]["away"]
                        tot1+=gh+ga
                        if gh>0 and ga>0: gg1+=1
                    time.sleep(0.8)
                    r2 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={f['teams']['away']['id']}&last=5", headers=HEAD, timeout=15).json()
                    gg2=0; tot2=0
                    for x in r2.get("response",[]):
                        gh=x["goals"]["home"]; ga=x["goals"]["away"]
                        tot2+=gh+ga
                        if gh>0 and ga>0: gg2+=1
                    media=(tot1+tot2)/10
                    perc=((gg1+gg2)/10)*100
                    if perc>=60:
                        lista.append((perc, f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} - GG {perc:.0f}% media {media:.2f}\n 🏆 {f['league']['name']} - {f['league']['country']}"))
                except Exception as e:
                    print(f"Errore GG {e}", flush=True)
            lista.sort(key=lambda x: x[0], reverse=True)
            if lista:
                send("⚽ LISTA GOL GOL - Top 3 ogni 2H\n\n" + "\n\n".join([x[1] for x in lista[:3]]))
            else:
                send("⚽ LISTA GOL GOL - Nessuna >60% al momento")

        print("Sleep 60s", flush=True)
        time.sleep(60)

    except Exception as e:
        print(f"ERRORE LOOP PRINCIPALE: {e}", flush=True)
        time.sleep(60)
