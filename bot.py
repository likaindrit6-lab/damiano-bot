
import os, time, requests, json
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

print("V6.5 AVVIO", flush=True)

def tg(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id":CHAT_ID,"text":t,"parse_mode":"HTML"}, timeout=10)
    except: pass

def api(url):
    try:
        r=requests.get(url, headers={"x-apisports-key":API_KEY}, timeout=15)
        print(f"API {r.status_code}", flush=True)
        if r.status_code==429:
            tg("⚠️ API FINITE - stop 10 min")
            time.sleep(600)
            return []
        return r.json().get("response",[])
    except Exception as e:
        print(f"ERR {e}", flush=True)
        return []

tg("✅ <b>BOT V6.5 ATTIVO - ANTI BLOCCO</b>")
print("BOT V6.5 LIVE", flush=True)

sent=set()
while True:
    try:
        now=datetime.now(pytz.timezone("Europe/Rome"))
        print(f"--- Check {now.strftime('%H:%M:%S')} ---", flush=True)
        
        lives=api("https://v3.football.api-sports.io/fixtures?live=all")
        print(f"Live: {len(lives)}", flush=True)

        count=0
        for m in lives:
            if count>=5: break  # controlla max 5 partite a giro per non bloccarsi
            fid=m["fixture"]["id"]
            minute=m["fixture"]["status"]["elapsed"] or 0
            if minute<15 or minute>80: continue
            
            # corner check
            stats=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
            corners=0
            for ts in stats:
                for s in ts.get("statistics",[]):
                    if "Corner" in s.get("type",""):
                        v=s.get("value") or 0
                        if isinstance(v,int): corners+=v
            
            if f"c{fid}" not in sent and corners>=4:
                gh=m["goals"]["home"] or 0
                ga=m["goals"]["away"] or 0
                tg(f"🚩 <b>CORNER {corners} al {minute}' {gh}-{ga}</b>\n{m['teams']['home']['name']} vs {m['teams']['away']['name']}")
                sent.add(f"c{fid}")
            
            count+=1
            time.sleep(1.2) # pausa per non far bannare API

        print("Fatto, dormo 90s", flush=True)
        time.sleep(90)

    except Exception as e:
        print(f"LOOP ERR {e}", flush=True)
        time.sleep(30)
