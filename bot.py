
import os, time, requests, json, threading
from datetime import datetime
import pytz
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")
FILE = "sent.json"
API_URL = "https://v3.football.api-sports.io"

app = Flask(__name__)
@app.route('/')
def home():
    return "BOT OK V7.2", 200

# --- memoria ---
def load():
    try:
        if os.path.exists(FILE):
            with open(FILE,"r") as f:
                d=json.load(f)
                return set(d.get("sent",[])), d.get("scores",{}), set(d.get("seguite",[])), d.get("last_gg",-1)
    except: pass
    return set(), {}, set(), -1

def save(a,b,c,d):
    try:
        with open(FILE,"w") as f: json.dump({"sent":list(a),"scores":b,"seguite":list(c),"last_gg":d},f)
    except: pass

sent, last_scores, seguite, last_gg_hour = load()

def tg(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":t,"parse_mode":"HTML"}, timeout=10)
    except: pass

def api_get(url, params=None):
    try:
        r=requests.get(url, headers={"x-apisports-key":API_KEY}, params=params, timeout=20)
        j=r.json()
        resp=j.get("response",[])
        print(f"API {r.status_code} {params} -> {len(resp)}", flush=True)
        if r.status_code==429:
            time.sleep(60)
            return []
        return resp
    except Exception as e:
        print(f"API ERR {e}", flush=True)
        return []

def get_live():
    lives=api_get(f"{API_URL}/fixtures", {"live":"all"})
    out=[]
    for f in lives:
        if f.get("fixture",{}).get("status",{}).get("short") in ["1H","HT","2H","ET","BT","P","INT","LIVE"]:
            out.append(f)
    print(f"LIVE FINALI: {len(out)}", flush=True)
    return out

def get_stats(fid):
    return api_get(f"{API_URL}/fixtures/statistics", {"fixture":fid})

def bot_loop():
    print("V7.2 LOOP PARTITO", flush=True)
    # ANTI-SPAM AVVIO: manda msg solo ogni 10 min
    try:
        f_path="/tmp/last_start.txt"
        now=time.time()
        last=0
        if os.path.exists(f_path):
            try: last=float(open(f_path).read())
            except: last=0
        if now-last>600:
            tg("✅ <b>BOT V7.2 STABILE - Fixato riavvio</b>\nOra resta acceso fisso")
            open(f_path,"w").write(str(now))
        else:
            print("Skip messaggio avvio, troppo vicino", flush=True)
    except: pass

    while True:
        try:
            now=datetime.now(pytz.timezone("Europe/Rome"))
            print(f"--- Check {now.strftime('%H:%M:%S')} ---", flush=True)
            lives=get_live()
            c=0
            for m in lives:
                if c>=8: break
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
                full=f"{m['league']['name']} - {m['teams']['home']['name']} vs {m['teams']['away']['name']}"
                if f"c{fid}" not in sent and corners>=3:
                    tg(f"🚩 <b>CORNER {corners} al {minute}' {gh}-{ga}</b>\n{full}")
                    sent.add(f"c{fid}")
                    save(sent,last_scores,seguite,last_gg_hour)
                c+=1
                time.sleep(1.2)
            print("Dormo 90s", flush=True)
            time.sleep(90)
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
            time.sleep(30)

threading.Thread(target=bot_loop, daemon=False).start()

if __name__ == "__main__":
    port=int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
