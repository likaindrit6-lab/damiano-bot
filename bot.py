
import os, time, requests, json
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")
FILE = "sent.json"
API_URL = "https://v3.football.api-sports.io"

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

def api_get(url, params=None):
    try:
        headers={"x-apisports-key":API_KEY}
        r=requests.get(url, headers=headers, params=params, timeout=20)
        j=r.json()
        resp=j.get("response",[])
        print(f"API {r.status_code} params={params} -> trovati {len(resp)}", flush=True)
        if r.status_code==429:
            print("429 PAUSA 60s", flush=True)
            time.sleep(60)
            return []
        return resp
    except Exception as e:
        print(f"API ERR {e}", flush=True)
        return []

def get_live():
    # FIX: prova solo live=all pulito
    lives = api_get(f"{API_URL}/fixtures", {"live":"all"})
    finali = []
    for f in lives:
        short = f.get("fixture",{}).get("status",{}).get("short","")
        if short in ["1H","HT","2H","ET","BT","P","INT","LIVE"]:
            finali.append(f)
    print(f"LIVE FINALI FILTRATI: {len(finali)}", flush=True)
    return finali

def get_stats(fid):
    return api_get(f"{API_URL}/fixtures/statistics", {"fixture":fid})

print("V7.0 FIX LIVE AVVIO", flush=True)
tg("✅ <b>BOT V7.0 FIX LIVE ATTIVO</b> - Cerca ogni 90s")

while True:
    try:
        now=datetime.now(pytz.timezone("Europe/Rome"))
        print(f"--- Check {now.strftime('%H:%M:%S')} ---", flush=True)
        
        lives=get_live()
        print(f"LIVE FINALI: {len(lives)}", flush=True)

        count=0
        for m in lives:
            if count>=8: break
            fid=m["fixture"]["id"]
            minute=m["fixture"]["status"]["elapsed"] or 0
            if minute<15 or minute>85: continue
            
            stats=get_stats(fid)
            corners=0
            for ts in stats:
                for s in ts.get("statistics",[]):
                    if "Corner" in s.get("type",""):
                        v=s.get("value")
                        if isinstance(v,int): corners+=v
            
            gh=m["goals"]["home"] or 0
            ga=m["goals"]["away"] or 0
            home=m['teams']['home']['name']
            away=m['teams']['away']['name']
            lega=m['league']['name']
            full=f"{lega} - {home} vs {away}"

            # FILTRO ABBASSATO A 3 PER STANOTTE
            if f"c{fid}" not in sent and corners>=3:
                tg(f"🚩 <b>CORNER {corners} al {minute}' {gh}-{ga}</b>\n{full}\nID:{fid}")
                sent.add(f"c{fid}")
                save(sent,last_scores,seguite,last_gg_hour)
                print(f"Inviato corner {fid} {corners}", flush=True)

            count+=1
            time.sleep(1.2)

        print("Fatto, dormo 90s", flush=True)
        time.sleep(90)
    except Exception as e:
        print(f"LOOP ERR {e}", flush=True)
        time.sleep(30)
