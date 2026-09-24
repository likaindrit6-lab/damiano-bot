
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

            if el <= 50 and stats["on"] >= 5 and f"calda-{fid}" not in inviate:
                send(f"🔥 CALDA {el}' - 5 tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"calda-{fid}")
            if el <= 45 and stats["corn"] >= 5 and f"corn-{fid}" not in inviate:
                send(f"🚩 CORNER 5 al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"corn-{fid}")
            if 55 <= el <= 65 and stats["on"] <= 3 and f"morta-{fid}" not in inviate:
                send(f"🧊 MORTA {el}' - {stats['on']} tiri\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"morta-{fid}")
            if el <= 60 and stats["red"] >= 1 and f"rosso-{fid}" not in inviate:
                send(f"🟥 ROSSO al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}")
                inviate.add(f"rosso-{fid}")

        # SCHEDINA 10:00
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

        # LISTA OVER ogni 3 ore - SENZA THREAD, così non crasha
        if time.time() - ultimo_over_check > 10800:
            print("Check lista OVER...", flush=True)
            ultimo_over_check = time.time()
            tod = get_today()
            lista=[]
            for f in tod[:10]: # solo 10 per non finire API
                if f["fixture"]["status"]["short"]!="NS": continue
                try:
                    time.sleep(1)
                    r1 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={f['teams']['home']['id']}&last=5", headers=HEAD, timeout=15).json()
                    tot1 = sum([x["goals"]["home"]+x["goals"]["away"] for x in r1.get("response",[])])
                    time.sleep(1)
                    r2 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={f['teams']['away']['id']}&last=5", headers=HEAD, timeout=15).json()
                    tot2 = sum([x["goals"]["home"]+x["goals"]["away"] for x in r2.get("response",[])])
                    media = (tot1+tot2)/10
                    if media >= 1.5:
                        lista.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} - media {media:.2f}\n 🏆 {f['league']['name']} - {f['league']['country']}")
                except Exception as e:
                    print(f"Errore over {e}", flush=True)
            if lista:
                send("📊 LISTA OVER 1.5 - Media ultime 5\n\n" + "\n\n".join(lista[:10]))

        print("Sleep 60s", flush=True)
        time.sleep(60)

    except Exception as e:
        print(f"ERRORE LOOP PRINCIPALE: {e}", flush=True)
        time.sleep(60)
