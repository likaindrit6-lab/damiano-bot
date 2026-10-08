import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g={}
av_s=set()
pre=set()
pre1=set()
cache={}
tripla_coda=[]
ultimo_invio_tripla=time.time()

try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V18.5 FINAL PULITO - {s}",200

def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({"keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        base=f"https://api.telegram.org/bot{BOT_TOKEN}"
        url=base+"/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA_JSON
        requests.post(url,json=payload,timeout=25)
    except: pass

def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def crea_bolla_15():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures: return f"Nessuna partita oggi {OGGI}"
        picks=[]; quota_tot=1.0
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            if len(picks)>=10: break
            if quota_tot>=3.35: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            orario=dt.strftime("%H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue
            try:
                best=None
                for bet in odds[0]["bookmakers"][0]["bets"]:
                    if "First Half" in bet["name"]: continue
                    if "Corners" in bet["name"]: continue
                    if "Cards" in bet["name"]: continue
                    for v in bet["values"]:
                        try:
                            q=float(v["odd"])
                            if 1.08 <= q <= 1.30:
                                if best is None or q > best["q"]:
                                    best={"m":bet["name"],"e":v["value"],"q":q}
                        except: continue
                if not best: continue
                if quota_tot*best["q"]>3.45: continue
                m_name=best["m"]; m_val=best["e"]
                if "Match Winner" in m_name:
                    if "Home" in m_val: txt="1"
                    elif "Away" in m_val: txt="2"
                    else: txt="X"
                elif "Double Chance" in m_name
