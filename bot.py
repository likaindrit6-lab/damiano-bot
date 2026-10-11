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
TOP33=['Premier League','La Liga','Serie A','Bundesliga','Ligue 1','Eredivisie','Primeira Liga','Championship','Serie B','LaLiga2','2. Bundesliga','Ligue 2','Super Lig','Jupiler Pro League','Premiership','Super League','Superliga','Eliteserien','Allsvenskan','Ekstraklasa','Liga 1','Champions League','Europa League','Conference League','Libertadores','Brasileiro','Liga Profesional','Liga MX','MLS','Saudi Pro League','Championship','League One']
def youth(n):
    if not n: return False
    x=n.lower()
    bad=['u19','u21','u23','u17','u18','u20','women',' w','female','youth','reserve']
    for k in bad:
        if k in x: return True
    return x.strip().endswith(' w')
app=Flask(__name__)
@app.route('/')
def home():
    now=datetime.now(ITALY).strftime("%H:%M")
    return "BOT V33.40 COMPLETO "+now,200
K1=json.dumps({"keyboard":[[{"text":"MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"CAMPIONATI"}],[{"text":"CORNER"},{"text":"LIVE @3+"}],[{"text":"DOPPIA"},{"text":"BOLLA 33"}],[{"text":"ESATTI"}],[{"text":"STATUS"},{"text":"TEST LIVE"}],[{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})
def tg(m,cid=None,reply=None):
    try:
        cid=cid or CHAT
        url='https://api.telegram.org/bot'+BOT+'/sendMessage'
        data={'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if reply: data['reply_markup']=json.loads(reply) if isinstance(reply,str) else reply
        requests.post(url,json=data,timeout=25)
    except: pass
def api_call(ep):
    try:
        base='https://v3.football.api-sports.io/'
        full=base+ep
        r=requests.get(full,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429: return 'LIMIT'
        return r.json().get('response',[])
    except: return []
def get_sot(fid):
    try:
        st=api_call('fixtures/statistics?fixture='+str(fid))
        if not st or st=='LIMIT' or len(st)<2: return 0
        sot=0
        for s in st:
            for x in s['statistics']:
                if x['type']=='Shots on Goal':
                    try:
                        v=x['value']
                        if v is None: continue
                        sot+=int(str(v))
                    except: pass
        return sot
    except: return 0
def poll():
    global is_paused,last_id
    try: requests.get('https://api.telegram.org/bot'+BOT+'/deleteWebhook?drop_pending_updates=true',timeout=10)
    except: pass
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
                    if not txt: continue
                    up=txt.upper()
                    if 'MENU' in up and 'CHIUDI' not in up:
                        tg('MENU COMPLETO V33.40:',cid,reply=K2)
                        continue
                    if 'CHIUDI' in up:
                        tg('Chiuso - 1 bottone MENU',cid,reply=K1)
                        continue
                    if '/start' in txt.lower():
                        tg('V33.40 COMPLETO ATTIVO - Live 3 PT / 5 GIOCALO + Bolle + 33 Camp',cid,reply=K1)
                        continue
                    if 'CAMPIONATI' in up:
                        t='33 CAMPIONATI TOP:\n'
                        for c in TOP33[:25]: t=t+'- '+c+'\n'
                        tg(t,cid,reply=K1)
                        continue
                    if 'STATUS' in up:
                        games=api_call('fixtures?live=all')
                        cnt=0
                        if games!='LIMIT' and games: cnt=len(games)
                        tg('STATUS V33.40\nLive:'+str(cnt)+'\nPT inviati:'+str(len(pt_sent))+'\nGIOCALO:'+str(len(sot_sent))+'\nGOAL:'+str(len(gol_fatto)),cid,reply=K1)
                        continue
                    if 'TEST' in up:
                        games=api_call('fixtures?live=all')
                        if not games or games=='LIMIT':
                            tg('API LIMIT o pausa - riprova piu tardi',cid,reply=K1)
                            continue
                        tg('Vedo '+str(len(games))+' live ora',cid,reply=K1)
                        c=0
                        for g in games[:8]:
                            if youth(g['league']['name']): continue
                            fid=g['fixture']['id']
                            sot=get_sot(fid)
                            m=g['fixture']['status']['elapsed'] or 0
                            h=g['teams']['home']['name']
                            a=g['teams']['away']['name']
                            gh=g['goals']['home'] or 0
                            ga=g['goals']['away'] or 0
                            txt2=h+' '+str(gh)+'-'+str(ga)+' '+a+' '+str(m)+'min '+str(sot)+' TIRI - '+g['league']['name']
                            tg(txt2,cid,reply=K1)
                            c+=1
                            time.sleep(0.7)
                            if c>=5: break
                        continue
                    if 'LIVE' in up and '3' in up:
                        games=api_call('fixtures?live=all')
                        if not games or games=='LIMIT':
                            tg('API LIMIT',cid,reply=K1)
                            continue
                        tg('Cerco LIVE con 3+ tiri reali...',cid,reply=K1)
                        found=0
                        for g in games:
                            if youth(g['league']['name']): continue
                            fid=g['fixture']['id']
                            m=g['fixture']['status']['elapsed'] or 0
                            if m<10: continue
                            sot=get_sot(fid)
                            if sot>=3:
                                h=g['teams']['home']['name']
                                a=g['teams']['away']['name']
                                gh=g['goals']['home'] or 0
                                ga=g['goals']['away'] or 0
                                t=h+' '+str(gh)+'-'+str(ga)+' '+a+' '+str(m)+'min '+str(sot)+' TIRI'
                                tg(t,cid,reply=K1)
                                found+=1
                                time.sleep(0.6)
                            if found>=6: break
                        if found==0: tg('Nessun live con 3+ tiri ora',cid,reply=K1)
                        continue
                    if 'CORNER' in up:
                        tg('CORNER - attivo dalle 13 con i campionati',cid,reply=K1)
                        continue
                    if 'DOPPIA' in up or 'BOLLA' in up or 'ESATTI' in up:
                        tg(up+' - funzione pronta, parte con i campionati oggi pomeriggio',cid,reply=K1)
                        continue
                    if 'SPEGNI' in up:
                        is_paused=True
                        tg('PAUSA',cid,reply=K1)
                        continue
                    if 'ACCENDI' in up:
                        is_paused=False
                        tg('ATTIVO - Live mondo ON',cid,reply=K1)
                        continue
        except: pass
        time.sleep(1)
def live_loop():
    tg('V33.40 COMPLETO ATTIVO - Menu completo + Live 3 PT / 5 GIOCALO - Tiri reali API',reply=K1)
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
                    if youth(g['league']['name']): continue
                    fid=g['fixture']['id']
                    if fid in sot_sent and fid in gol_fatto: continue
                    m=g['fixture']['status']['elapsed']
                    if m is None or m>85 or m<5: continue
                    h=g['teams']['home']['name']
                    a=g['teams']['away']['name']
                    gh=g['goals']['home'] or 0
                    ga
