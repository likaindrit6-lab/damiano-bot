
import os, time, requests, json
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")
FILE = "sent.json"

def load():
    try:
        if os.path.exists(FILE):
            with open(FILE,"r") as f:
                d=json.load(f)
                return set(d.get("sent",[])), d.get("scores",{}), set(d.get("seguite",[])), d.get("last_gg",-1)
    except: pass
    return set(), {}, set(), -1

def save(s_set, sc_dict, seg_set, last_gg):
    try:
        with open(FILE,"w") as f:
            json.dump({"sent":list(s_set),"scores":sc_dict,"seguite":list(seg_set),"last_gg":last_gg},f)
    except: pass

sent, last_scores, seguite, last_gg_hour = load()

def tg(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id":CHAT_ID,"text":t,"parse_mode":"HTML"}, timeout=10)
    except: pass

def api_get(url):
    try:
        r=requests.get(url, headers={"x-apisports-key":API_KEY}, timeout=20)
        print(f"API {r.status_code} {url[-35:]}", flush=True)
        j=r.json()
        # stampa quanti ne ha trovati
        resp=j.get("response",[])
        print(f"-> trovati {len(resp)}", flush=True)
        if r.status_code==429:
            print("429 PAUSA 10 MIN", flush=True)
            time.sleep(600)
            return []
        return resp
    except Exception as e:
        print(f"API ERR {e}", flush=True)
        return []

def get_live():
    # PROVA 1 - quella normale
    lives = api_get("https://v3.football.api-sports.io/fixtures?live=all")
    if len(lives)>0:
        return lives
    # PROVA 2 - se la prima da 0, prova con status live
    print("Provo backup live...", flush=True)
    lives2 = api_get("https://v3.football.api-sports.io/fixtures?status=1H-HT-2H-ET-BT-P-INT&timezone=Europe/Rome")
    return lives2

def get_stats(fid):
    return api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")

print("V6.8 PAGAMENTO AVVIO", flush=True)
tg("✅ <b>BOT V6.8 ATTIVO - PIANO 19€</b>")

while True:
    try:
        now=datetime.now(pytz.timezone("Europe/Rome"))
        print(f"--- Check {now.strftime('%H:%M:%S')} ---", flush=True)
        
        lives=get_live()
        print(f"LIVE FINALI: {len(lives)}", flush=True)

        count=0
        for m in lives:
            if count>=6: break
            fid=m["fixture"]["id"]
            minute=m["fixture"]["status"]["elapsed"] or 0
            if minute<15 or minute>80: continue
            
            stats=get_stats(fid)
            corners=0
            for ts in stats:
                for s in ts.get("statistics",[]):
                    if "Corner" in s.get("type",""):
                        v=s.get("value") or 0
                        if isinstance(v,int): corners+=v
            
            gh=m["goals"]["home"] or 0
            ga=m["goals"]["away"] or 0
            full=f"{m['league']['name']} - {m['teams']['home']['name']} vs {m['teams']['away']['name']}"

            if f"c{fid}" not in sent and corners>=4:
                tg(f"🚩 <b>CORNER {corners} al {minute}' {gh}-{ga}</b>\n{full}")
                sent.add(f"c{fid}")
                save(sent,last_scores,seguite,last_gg_hour)

            count+=1
            time.sleep(1.5)

        print("Fatto, dormo 90s", flush=True)
        time.sleep(90)
    except Exception as e:
        print(f"LOOP ERR {e}", flush=True)
        time.sleep(30)
