
import os, requests, time, random, threading
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL") or os.getenv("API_KEY")
HEAD = {"x-apisports-key": API_KEY}

try: requests.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)
except: pass

inviate = set()
ID = random.randint(1000,9999)

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": t}, timeout=20)
    except: pass

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
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=20).json()
        return r.get("response", [])
    except: return []

def avg_last5(team_id):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEAD, timeout=15).json()
        tot=0; n=0
        for f in r.get("response", []):
            tot+= f["goals"]["home"]+f["goals"]["away"]; n+=1
        return tot/n if n else 0
    except: return 0

# THREAD LISTA OVER - sfrutta le tue 7200 chiamate con pausa 1 sec
def thread_over():
    while True:
        try:
            tod = get_today()
            lista=[]
            for f in tod[:15]: # prime 15 di oggi
                if f["fixture"]["status"]["short"]!="NS": continue
                time.sleep(1)
                m1=avg_last5(f["teams"]["home"]["id"])
                time.sleep(1)
                m2=avg_last5(f["teams"]["away"]["id"])
                media=(m1+m2)/2
                if media>=1.5:
                    lista.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} - media {media:.2f}\n 🏆 {f['league']['name']} - {f['league']['country']}")
            if lista:
                send("📊 LISTA OVER 1.5 - Media ultime 5 >=1.5 gol\n\n" + "\n\n".join(lista[:10]))
            time.sleep(3600*3) # ogni 3 ore, hai chiamate a pagamento
        except: time.sleep(3600)

threading.Thread(target=thread_over, daemon=True).start()
send(f"✅ BOT DAMI RENDER FINALE {ID} - 7200 chiamate ON - Gira!")

# LOOP LIVE
while True:
    try:
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=15).json().get("response", [])
        for m in live:
            el = m["fixture"]["status"]["elapsed"] or 0
            if el<2 or m["goals"]["home"]!=0 or m["goals"]["away"]!=0: continue
            fid=m["fixture"]["id"]
            casa=m["teams"]["home"]["name"]; fuori=m["teams"]["away"]["name"]
            league=m["league"]["name"]; country=m["league"]["country"]
            stats=get_stats(fid)
            if el<=50 and stats["on"]>=5 and f"calda-{fid}" not in inviate:
                send(f"🔥 CALDA {el}' - 5 tiri\n{casa} vs {fuori}\n🏆 {league} - {country}"); inviate.add(f"calda-{fid}")
            if el<=45 and stats["corn"]>=5 and f"corn-{fid}" not in inviate:
                send(f"🚩 CORNER 5 al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}"); inviate.add(f"corn-{fid}")
            if 55<=el<=65 and stats["on"]<=3 and f"morta-{fid}" not in inviate:
                send(f"🧊 MORTA {el}' - {stats['on']} tiri\n{casa} vs {fuori}\n🏆 {league} - {country}"); inviate.add(f"morta-{fid}")
            if el<=60 and stats["red"]>=1 and f"rosso-{fid}" not in inviate:
                send(f"🟥 ROSSO al {el}'\n{casa} vs {fuori}\n🏆 {league} - {country}"); inviate.add(f"rosso-{fid}")

        now=datetime.now()
        if now.hour==10 and now.minute<5:
            key=f"quota-{now.strftime('%Y-%m-%d')}"
            if key not in inviate:
                tod=get_today()
                if len(tod)>=3:
                    txt="💰 SCHEDINA 10:00 - Quota 1.60/1.70\n\n"
                    for i,f in enumerate(tod[:3],1):
                        txt+=f"{i}. {f['teams']['home']['name']} vs {f['teams']['away']['name']} - 1X / Over 0.5\n 🏆 {f['league']['name']} - {f['league']['country']}\n"
                    txt+="\nQuota finale stimata: 1.70"
                    send(txt); inviate.add(key)
        time.sleep(45) # con piano a pagamento puoi fare ogni 45 sec
    except: time.sleep(60)
