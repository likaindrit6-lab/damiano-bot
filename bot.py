import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g,av_s,pre,pre1,cache={},set(),set(),set(),{}
tripla_coda=[]
ultimo_invio_tripla=time.time()

try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except:
    pass

app=Flask(__name__)
@app.route('/')
def home():
    stato="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V13.2 LINK FIX - {stato}",200

def run_flask():
    from waitress import serve
    serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({
    "keyboard":[["ACCONDI","SPEGNI"],["BOLLA","STATUS"]],
    "resize_keyboard":True,"is_persistent":True
})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera:
            payload["reply_markup"]=TASTIERA_JSON
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json=payload,timeout=25)
    except:
        pass

def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429:
            return "LIMIT"
        return r.json().get("response",[])
    except:
        return []

def get_stat(arr,name):
    for s in arr:
        if s.get('type')==name:
            try:
                return int(str(s.get('value') or 0).replace('%','').strip() or 0)
            except:
                return 0
    return 0

def get_flag(p):
    m={"Italy":"IT","England":"GB","Spain":"ES","Germany":"DE","France":"FR","Portugal":"PT","Netherlands":"NL","Belgium":"BE","Turkey":"TR","Brazil":"BR","Argentina":"AR","USA":"US","Australia":"AU","Japan":"JP","South Korea":"KR"}
    return m.get(p,p[:2].upper())

def get_tiri(fid):
    try:
        d=cache.get(fid)
        if not d or time.time()-d.get('time',0)>180:
            s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
            if s and len(s)>=2:
                sot=get_stat(s[0]['statistics'],'Shots on Goal')
