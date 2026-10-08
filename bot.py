import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")

ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
ultimo_gol={}
ultima_schedina_ora=-1
schedina_attiva=[]
schedina_notificata=set()
live_inviate=set()

if BOT_TOKEN:
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
        print("Webhook pulito",flush=True)
    except Exception as e:
        print(e,flush=True)

app=Flask(__name__)
@app.route('/')
def home(): return "BOT V37 DOPPIA+MULTIGOL 1-5",200
@app.route('/health')
def health(): return "OK",200

TASTIERA=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BLASONATE LUN-DOM","PARTITE OGGI"],["SCHEDINA ORA","TOKEN"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id or CHAT_ID
        if not BOT_TOKEN or not cid: return
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA
        if len(m)>3800:
            for i in range(0,len(m),3800):
                payload["text"]=m[i:i+3800]
                if i>0: payload.pop("reply_markup",None)
                requests.post(url,json=payload,timeout=15)
                time.sleep(0.3)
        else: requests.post(url,json=payload,timeout=15)
    except Exception as e: print(e,flush=True)

def api_get(url):
    if is_paused: return []
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=15)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def crea_blasonate():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if fx=="LIMIT": return "Limite API - riprovo dopo"
        big=["milan","inter","juventus","juve","napoli","roma","lazio","atalanta","fiorentina","real madrid","bar
