import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_id=0;sot_sent=set();gol_tracker={};gol_fatto=set();pt_sent=set()
def youth(n):
    if not n: return False
    x=n.lower()
    return any(k in x for k in ['u19','u21','u23','u17','u18','u20','women',' w','female','youth','reserve'])
app=Flask(__name__)
@app.route('/')
def home(): return f'BOT V33.36 - {datetime.now(ITALY).strftime("%H:%M")}',200
K1=json.dumps({"keyboard":[[{"text":"☰ MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"STATUS"},{"text":"TEST LIVE"}],[{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"⬇️ CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})
def tg(m,cid=None,reply=None):
    try:
        cid=cid or CHAT
        requests.post(f'https://api.telegram.org/bot{BOT}/sendMessage',json={'chat_id':cid,'text':m,'parse_mode':'HTML','reply_markup':json.loads(reply) if isinstance(reply,str) else reply},timeout=25)
    except: pass
def api(u):
    try:
        r=requests.get(u,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429: return 'LIMIT'
        return r.json().get('response',[])
    except: return []
def get_sot(fid):
    try:
        st=api(f'https://v3.football.api-sports.io/fi
