import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN')
CHAT=os.getenv('CHAT_ID')
KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_id=0
sot_sent=set()
gol_tracker={}
gol_fatto=set()
pt_sent=set()

def youth(n):
    if not n: return False
    x=n.lower()
    for k in ['u19','u21','u23','u17','women',' w','female','youth']:
        if k in x: return True
    return False

app=Flask(__name__)
@app.route('/')
def home():
    now=datetime.now(ITALY).strftime("%H:%M")
    return "BOT V33.42 OK "+now,200

K1=json.dumps({"keyboard":[[{"text":"MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"CAMPIONATI"}],[{"text":"CORNER"},{"text":"LIVE @3+"}],[{"text":"DOPPIA"},{"text":"BOLLA 33"}],[{"text":"ESATTI"}],[{"text":"STATUS"},{"text":"TEST LIVE"}],[{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})

def tg(m,cid=None,reply=None):
    try:
        cid=cid or CHAT
        url='https://api.telegram.org/bot'+BOT+'/sendMessage'
        data={'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if reply:
            data['reply_markup']=json.loads(reply) if isinstance(reply,str) else reply
        requests.post(url,json=data,timeout=25)
    except Exception:
        pass

def api_call(ep):
    try:
        base='https://v3.football.api-sports.io/'
        r=requests.get(base+ep,headers={'x-apisports-key':KEY
