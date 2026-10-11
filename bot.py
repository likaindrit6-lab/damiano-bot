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
    if not n:
        return False
    x=n.lower()
    return any(k in x for k in ['u19','u21','u23','u17','women',' w','female','youth','reserve'])
app=Flask(__name__)
@app.route('/')
def home():
    return f'BOT V33.37 OK {datetime.now(ITALY).strftime("%H:%M")}',200
K1=json.dumps({"keyboard":[[{"text":"☰ MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"STATUS"},{"text":"TEST LIVE"}],[{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"⬇️ CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})
def tg(m,cid=None,reply=None):
    try:
        cid=cid or CHAT
        url='https://api.telegram.org/bot'+BOT+'/sendMessage'
        data={'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if reply:
            data['reply_markup']=json.loads(reply) if isinstance(reply,str) else reply
        requests.post(url,json=data,timeout=25)
    except:
        pass
def api_call(ep):
    try:
        base='https://v3.football.api-sports.io/'
        full=base+ep
        r=requests.get(full,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429:
            return 'LIMIT'
        return r.json().get('response',[])
    except:
        return []
def get_sot(fid):
    try:
        st=api_call('fixtures/statistics?fixture='+str(fid))
        if not st or st=='LIMIT' or len(st)<2:
            return 0
        sot=0
        for s in st:
            for x in s['statistics']:
                if x['type']=='Shots on Goal':
                    try:
                        sot+=int(str(x['value'] or 0))
                    except:
                        pass
        return sot
    except:
        return 0
def poll():
    global is_paused,last_id
    try:
        u='https://api.telegram.org/bot'+BOT+'/deleteWebhook?drop_pending_updates=true'
        requests.get(u,timeout=10)
    except:
        pass
    while True:
        try:
            u='https://api.telegram.org/bot'+BOT+'/getUpdates?offset='+str(last_id+1)+'&timeout=20'
            r=requests.get(u,timeout=35).json()
            if r.get('ok'):
                for upd in r.get('result',[]):
                    last_id=upd['update_id']
                    msg=upd.get('message',{})
                    txt=(msg.get('text') or '').strip()
                    cid=msg.get('chat',{}).get('id')
                    if not txt:
                        continue
                    up=txt.upper()
                    if 'MENU' in up and 'CHIUDI' not in up:
                        tg('MENU:',cid,reply=K2)
                        continue
                    if 'CHIUDI' in up:
                        tg('Chiuso',cid,reply=K1)
                        continue
                    if '/start' in txt.lower():
                        tg('V33.37 FIX ATTIVO',cid,reply=K1)
                        continue
                    if 'STATUS' in up:
                        games=api_call('fixtures?live=all')
                        cnt=len(games) if games!='LIMIT' else 0
                        tg(f'Live:{cnt} PT:{len(pt_sent)} GIOCALO:{len(sot_sent)}',cid,reply=K1)
                        continue
                    if 'TEST' in up:
                        games=api_call('fixtures?live=all')
                        if not games or games=='LIMIT':
                            tg('API LIMIT',cid,reply=K1)
                            continue
                        tg(f'Vedo {len(games)} live',cid
