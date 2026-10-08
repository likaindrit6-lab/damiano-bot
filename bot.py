import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0

try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except:
    pass

app=Flask(__name__)
@app.route('/')
def home():
    return f"BOT OK - {datetime.now(ITALY).strftime('%H:%M')}",200

def run_flask():
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))

threading.Thread(target=run_flask,daemon=True).start()

TASTIERA=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BOLLA"],["STATUS"]],"resize_keyboard":True})

def tg(m,cid=None,kb=False):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        p={"chat_id":cid if cid else CHAT_ID,"text":m,"parse_mode":"HTML"}
        if kb:
            p["reply_markup"]=TASTIERA
        requests.post(url,json=p,timeout=20)
    except:
        pass

def api_get(u):
    try:
        r=requests.get(u,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=25)
        if r.status_code==429:
            return "LIMIT"
        return r.json().get("response",[])
    except:
        return []

def crea_bolla_15():
    try:
        picks=[]
        quota_tot=1.0
        BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly","Amateur","Club Friend"]
        for gg in range(3):
            if len(picks)>=20:
                break
            giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
            fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
            if not fixtures:
                continue
            for p in sorted(fixtures,key=lambda x:x["fixture"]["timestamp"]):
                if len(picks)>=20:
                    break
                if any(b.lower() in p["league"]["name"].lower() for b in BAN):
                    continue
                fid=p["fixture"]["id"]
                dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
                if dt<datetime.now(ITALY):
                    continue
                home=p["teams"]["home"]["name"]
                away=p
