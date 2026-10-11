import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_id=0;sot_sent=set();gol_tracker={};gol_fatto=set();av_s_first=set()
TOP={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}
EU=set(TOP.keys());IDS=set(TOP.values())
def youth(n): return any(k in n.lower() for k in ['u19','u21','women',' w','youth']) if n else False
def is_top(f):
    try: return f['league']['country'] in EU and f['league']['id'] in IDS and not youth(f['league']['name'])
    except: return False
app=Flask(__name__)
@app.route('/')
def home(): return f'V33.33 COMPACT 1 BOTTONE',200

# 1 BOTTONE SOLO COME IERI!
K1=json.dumps({"keyboard":[[{"text":"☰ MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"CAMPIONATI"}],[{"text":"CORNER"},{"text":"LIVE @3+"}],[{"text":"DOPPIA"},{"text":"BOLLA 33"}],[{"text":"ESATTI"}],[{"text":"STATUS"},{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"⬇️ CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})

def tg(m,cid=None,reply=None):
    try:
        cid=cid or CHAT
        requests.post(f'https://api.telegram.org/bot{BOT}/sendMessage',json={'chat_id':cid,'text':m,'parse_mode':'HTML','reply_markup':json.loads(reply) if isinstance(reply,str) else reply},timeout=20)
    except: pass
def api(u):
    try:
        r=requests.get(u,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429: return 'LIMIT'
        return r.json().get('response',[])
    except: return []
def poll():
    global is_paused,last_id
    try: requests.get(f'https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true',timeout=10)
    except: pass
    while True:
        try:
            r=requests.get(f'https://api.telegram.org/bot{BOT}/getUpdates?offset={last_id+1}&timeout=20',timeout=30).json()
            if r.get('ok'):
                for u in r.get('result',[]):
                    last_id=u['update_id'];txt=(u.get('message',{}).get('text') or '').strip();cid=u.get('message',{}).get('chat',{}).get('id')
                    if not txt: continue
                    if 'MENU' in txt.upper() and 'CHIUDI' not in txt.upper(): tg('SCEGLI:',cid,reply=K2);continue
                    if 'CHIUDI' in txt.upper(): tg('Menu chiuso',cid,reply=K1);continue
                    if '/start' in txt.lower(): tg('BOT V33.33 - 1 BOTTONE COME IERI - Japan OFF',cid,reply=K1);continue
                    if 'STATUS' in txt.upper(): tg('V33.33 OK - Solo EUROPA 33',cid,reply=K1);continue
                    if 'SPEGNI' in txt.upper(): is_paused=True;tg('PAUSA',cid,reply=K1);continue
                    if 'ACCENDI' in txt.upper(): is_paused=False;tg('ATTIVO',cid,reply=K1);continue
        except: pass
        time.sleep(1)
def live_loop():
    tg('V33.33 ATTIVO - 1 bottone MENU come ieri - Clicchi apre/chiude - Japan filtrato!',reply=K1)
    while True:
        try:
            if is_paused: time.sleep(30);continue
            now=datetime.now(ITALY)
            if 0<=now.hour<7: time.sleep(300);continue
            games=api('https://v3.football.api-sports.io/fixtures?live=all')
            if games=='LIMIT': time.sleep(3600);continue
            if not games: time.sleep(60);continue
            for g in games:
                try:
                    if not is_top(g): continue
                    fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
                    if m is None: continue
                    h=g['teams']['home']['name'];a=g['teams']['away']['name'];gh=g['goals']['home'] or 0;ga=g['goals']['away'] or 0;tot=gh+ga
                    st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0
                    if st and len(st)>=2:
                        for s in st:
                            for x in s['statistics']:
                                if x['type']=='Shots on Goal':
                                    try: sot+=int(str(x['value'] or 0))
                                    except: pass
                    if tot>sot and sot>0: continue
                    c=g['league']['country']
                    if fid not in av_s_first and m<=45 and sot>=3: tg(f"PRIMO TEMPO {h} {gh}-{ga} {a} - {sot} TIRI\n{c}",reply=K1);av_s_first.add(fid)
                    if fid not in sot_sent and m<=70 and sot>=6: tg(f"GIOCALO! {h} {gh}-{ga} {a} - {sot} TIRI al {m}'\n{c}",reply=K1);sot_sent.add(fid);gol_tracker[fid]=tot
                    if fid in sot_sent and fid not in gol_fatto and tot>gol_tracker.get(fid,0): tg(f"GOAL! {h} {gh}-{ga} {a}\n{c} - {sot} TIRI",reply=K1);gol_fatto.add(fid)
                except: continue
            time.sleep(45)
        except: time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
