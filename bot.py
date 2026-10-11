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
    bad=['u19','u21','u23','u17','u18','u20','women',' w','female','youth','reserve']
    for k in bad:
        if k in x:
            return True
    return x.strip().endswith(' w')
app=Flask(__name__)
@app.route('/')
def home():
    now=datetime.now(ITALY).strftime("%H:%M")
    return "BOT V33.39 OK "+now,200
K1=json.dumps({"keyboard":[[{"text":"MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"STATUS"},{"text":"TEST LIVE"}],[{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})
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
        if not st or st=='LIMIT':
            return 0
        if len(st)<2:
            return 0
        sot=0
        for s in st:
            for x in s['statistics']:
                if x['type']=='Shots on Goal':
                    try:
                        v=x['value']
                        if v is None:
                            continue
                        sot+=int(str(v))
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
                        tg('Chiuso - 1 bottone',cid,reply=K1)
                        continue
                    if '/start' in txt.lower():
                        tg('V33.39 FIX ATTIVO - Live mondo - Tiri reali',cid,reply=K1)
                        continue
                    if 'STATUS' in up:
                        games=api_call('fixtures?live=all')
                        cnt=0
                        if games!='LIMIT' and games:
                            cnt=len(games)
                        tg('Live:'+str(cnt)+' PT:'+str(len(pt_sent))+' GIOCALO:'+str(len(sot_sent)),cid,reply=K1)
                        continue
                    if 'TEST' in up:
                        games=api_call('fixtures?live=all')
                        if not games or games=='LIMIT':
                            tg('API LIMIT',cid,reply=K1)
                            continue
                        tg('Vedo '+str(len(games))+' live',cid,reply=K1)
                        c=0
                        for g in games[:6]:
                            if youth(g['league']['name']):
                                continue
                            fid=g['fixture']['id']
                            sot=get_sot(fid)
                            m=g['fixture']['status']['elapsed'] or 0
                            h=g['teams']['home']['name']
                            a=g['teams']['away']['name']
                            gh=g['goals']['home'] or 0
                            ga=g['goals']['away'] or 0
                            txt2=h+' '+str(gh)+'-'+str(ga)+' '+a+' '+str(m)+'min '+str(sot)+' TIRI'
                            tg(txt2,cid,reply=K1)
                            c+=1
                            time.sleep(0.7)
                            if c>=4:
                                break
                        continue
                    if 'SPEGNI' in up:
                        is_paused=True
                        tg('PAUSA',cid,reply=K1)
                        continue
                    if 'ACCENDI' in up:
                        is_paused=False
                        tg('ATTIVO',cid,reply=K1)
                        continue
        except:
            pass
        time.sleep(1)
def live_loop():
    tg('V33.39 ATTIVO - 3 PT / 5 GIOCALO - Tiri reali - Testato',reply=K1)
    while True:
        try:
            if is_paused:
                time.sleep(30)
                continue
            now=datetime.now(ITALY)
            if 0<=now.hour<7:
                time.sleep(300)
                continue
            games=api_call('fixtures?live=all')
            if games=='LIMIT':
                time.sleep(3600)
                continue
            if not games:
                time.sleep(60)
                continue
            for g in games:
                try:
                    if youth(g['league']['name']):
                        continue
                    fid=g['fixture']['id']
                    if fid in sot_sent and fid in gol_fatto:
                        continue
                    m=g['fixture']['status']['elapsed']
                    if m is None or m>85 or m<5:
                        continue
                    h=g['teams']['home']['name']
                    a=g['teams']['away']['name']
                    gh=g['goals']['home'] or 0
                    ga=g['goals']['away'] or 0
                    tot=gh+ga
                    sot=get_sot(fid)
                    if sot==0:
                        continue
                    if tot>sot:
                        continue
                    if fid not in pt_sent and m<=50 and sot>=3:
                        t='PRIMO TEMPO '+h+' '+str(gh)+'-'+str(ga)+' '+a+' - '+str(sot)+' TIRI al '+str(m)+'min'
                        tg(t,reply=K1)
                        pt_sent.add(fid)
                    if fid not in sot_sent and sot>=5:
                        t='GIOCALO! '+h+' '+str(gh)+'-'+str(ga)+' '+a+' - '+str(sot)+' TIRI al '+str(m)+'min '+g['league']['name']
                        tg(t,reply=K1)
                        sot_sent.add(fid)
                        gol_tracker[fid]=tot
                    if fid in sot_sent and fid not in gol_fatto and tot>gol_tracker.get(fid,0):
                        t='GOAL! '+h+' '+str(gh)+'-'+str(ga)+' '+a+' - HA SEGNATO!'
                        tg(t,reply=K1)
                        gol_fatto.add(fid)
                    time.sleep(0.8)
                except:
                    continue
            time.sleep(60)
        except:
            time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
