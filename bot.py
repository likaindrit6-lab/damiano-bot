import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN')
CHAT=os.getenv('CHAT_ID')
KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
ROME=ZoneInfo("Europe/Rome")
is_paused=False
last_id=0
av_g={}
av_s=set()
pre=set()
pre1=set()
cache={}
LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203}
app=Flask(__name__)
@app.route('/')
def home():
    now_it=datetime.now(ITALY)
    txt=now_it.strftime("%H:%M:%S")
    return f'BOT V22 LIVE DOPPIA BOLLA AMERICANO - {txt}',200
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["MODELLO AMERICANO 33"],["STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False):
    try:
        cid=cid or CHAT
        if not cid or not BOT:
            return
        base=f'https://api.telegram.org/bot{BOT}'
        pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if keys:
            pay['reply_markup']=json.loads(TAST)
        requests.post(base+'/sendMessage',json=pay,timeout=25)
    except:
        pass
def api(url):
    try:
        r=requests.get(url,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429:
            return 'LIMIT'
        j=r.json()
        return j.get('response',[])
    except:
        return []
def poll():
    global is_paused,last_id
    try:
        if BOT:
            requests.get(f'https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true',timeout=10)
    except:
        pass
    while True:
        try:
            if not BOT:
                time.sleep(60)
                continue
            base=f'https://api.telegram.org/bot{BOT}'
            url=base+f'/getUpdates?offset={last_id+1}&timeout=20'
            r=requests.get(url,timeout=30).json()
            if r.get('ok'):
                for u in r.get('result',[]):
                    last_id=u['update_id']
                    msg=u.get('message',{})
                    txt=(msg.get('text') or '').strip()
                    low=txt.lower()
                    cid=msg.get('chat',{}).get('id')
                    if not txt:
                        continue
                    if 'spegni' in low:
                        is_paused=True
                        tg('⏸️ PAUSA',cid,True)
                    elif 'accendi' in low or '/start' in low:
                        is_paused=False
                        tg('▶️ ATTIVO V22 - LIVE OK',cid,True)
                    elif 'status' in low:
                        st='PAUSA' if is_paused else 'ATTIVO'
                        tg(f'STATUS: {st}',cid,True)
                    elif 'doppia' in low:
                        tg('🔎 Calcolo DOPPIA ALTA %...',cid,True)
                        run_doppia(cid)
                    elif 'bolla' in low:
                        tg('🔎 Calcolo BOLLA 33 NAZIONI...',cid,True)
                        run_bolla(cid)
                    elif 'americano' in low:
                        tg('🔎 Calcolo MODELLO AMERICANO 33...',cid,True)
                        run_americano(cid)
        except:
            pass
        time.sleep(2)
def get_fixtures_today():
    today=datetime.now(ROME).strftime('%Y-%m-%d')
    url=f'https://v3.football.api-sports.io/fixtures?date={today}'
    return api(url)
def run_doppia(cid=None):
    data=get_fixtures_today()
    out=[]
    for f in data:
        try:
            fid=f['fixture']['id']
            if fid in av_g:
                continue
            g=f['goals']
            h=g['home']
            a=g['away']
            if h is None or a is None:
                continue
            tot=h+a
            if tot>=2:
                home=f['teams']['home']['name']
                away=f['teams']['away']['name']
                out.append(f'{home}-{away} {h}-{a}')
        except:
            continue
    if not out:
        tg('DOPPIA: Nessun match con 2+ goal al momento',cid,True)
    else:
        msg='🔥 DOPPIA ALTA %\n'+'\n'.join(out[:20])
        tg(msg,cid,True)
def run_bolla(cid=None):
    data=get_fixtures_today()
    sel=[]
    for f in data[:33]:
        try:
            home=f['teams']['home']['name']
            away=f['teams']['away']['name']
            sel.append(f'{home} vs {away}')
        except:
            continue
    if not sel:
        tg('BOLLA: Nessun match oggi',cid,True)
        return
    msg='🌍 BOLLA EUROPA 33 NAZIONI\n'+'\n'.join([f'{i+1}. {m}' for i,m in enumerate(sel[:33])])
    tg(msg,cid,True)
def run_americano(cid=None):
    data=get_fixtures_today()
    picks=[]
    for f in data[:33]:
        try:
            home=f['teams']['home']['name']
            away=f['teams']['away']['name']
            picks.append(f'{home} - {away}')
        except:
            continue
    if not picks:
        tg('AMERICANO: Nessun match oggi',cid,True)
        return
    lines=[]
    for i,m in enumerate(picks[:33],1):
        lines.append(f'{i}. {m} | ML | O/U')
    msg='🇺🇸 MODELLO AMERICANO 33\n'+'\n'.join(lines)
    tg(msg,cid,True)
def live_loop():
    tg('✅ BOT V22 COMPLETO - LIVE + DOPPIA + BOLLA + AMERICANO ATTIVO',keys=True)
    while True:
        try:
            if is_paused:
                time.sleep(30)
                continue
            time.sleep(60)
        except:
            time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0',port=port)
