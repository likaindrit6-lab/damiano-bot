import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN')
CHAT=os.getenv('CHAT_ID')
KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;last_bolla_hour=-1
sot_sent=set();gol_tracker={};gol_fatto=set();av_s_first=set();high_sent=set()
TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}
EUROPA_33=set(TOP_LEAGUES.keys())
TOP_IDS=set(TOP_LEAGUES.values())
def is_youth_league(name):
    if not name: return False
    n=name.lower()
    bad=['u19','u21','u23','u17','u18','u20','women',' w','female','youth','reserve','academy','world']
    if n.strip().endswith(' w'): return True
    return any(x in n for x in bad)
def is_top_match(f):
    try:
        if is_youth_league(f['league']['name']): return False
        if f['league']['country'] not in EUROPA_33: return False
        if f['league']['id'] not in TOP_IDS: return False
        return True
    except: return False
app=Flask(__name__)
@app.route('/')
def home(): return f'BOT V33.32 FIX JAPAN - {datetime.now(ITALY).strftime("%H:%M")}',200
TAST_MAIN=json.dumps({"keyboard":[[{"text":"CAMPIONATI"}],[{"text":"CORNER"},{"text":"LIVE @3+"}],[{"text":"DOPPIA"},{"text":"BOLLA 33"}],[{"text":"ESATTI"}],[{"text":"STATUS"},{"text":"SPEGNI"},{"text":"ACCENDI"}]],"resize_keyboard":True,"is_persistent":True})
TAST_NAZIONI=json.dumps({"keyboard":[[{"text":"ITALY"},{"text":"ENGLAND"},{"text":"SPAIN"}],[{"text":"GERMANY"},{"text":"FRANCE"},{"text":"NETHERLANDS"}],[{"text":"PORTUGAL"},{"text":"BELGIUM"},{"text":"TURKEY"}],[{"text":"INDIETRO"},{"text":"MENU"}]],"resize_keyboard":True,"is_persistent":True})
def tg(m,cid=None,reply=None):
    try:
        cid=cid or CHAT
        if not cid or not BOT: return
        base=f'https://api.telegram.org/bot{BOT}';pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if reply: pay['reply_markup']=json.loads(reply) if isinstance(reply,str) else reply
        requests.post(base+'/sendMessage',json=pay,timeout=25)
    except: pass
def api(url):
    try:
        r=requests.get(url,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429: return 'LIMIT'
        return r.json().get('response',[])
    except: return []
def get_double_chance(fid):
    try:
        data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
        if not data or data=='LIMIT': return None
        for book in data[0].get('bookmakers',[])[:3]:
            for bet in book.get('bets',[]):
                if 'Double Chance' in bet['name']:
                    best=None;best_odd=10
                    for v in bet['values']:
                        try:
                            odd=float(v['odd'])
                            if odd<best_odd: best_odd=odd;best=v['value']
                        except: continue
                    if best:
                        if 'Home/Draw' in best: return f"1X @ {best_odd}"
                        if 'Draw/Away' in best: return f"X2 @ {best_odd}"
                        if 'Home/Away' in best: return f"12 @ {best_odd}"
    except: pass
    return None
def get_fixtures_today():
    today=datetime.now(ROME).strftime('%Y-%m-%d')
    return api(f'https://v3.football.api-sports.io/fixtures?date={today}')
def run_bolla(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('BOLLA: Limite API',cid,reply=TAST_MAIN);return
    sel=[]
    for country,top_id in TOP_LEAGUES.items():
        found=None
        for f in data:
            if f['league']['id']==top_id and f['league']['country']==country:
                if is_youth_league(f['league']['name']): continue
                if f['fixture']['status']['short']!='NS': continue
                found=f;break
        if not found: continue
        fid=found['fixture']['id'];ora=found['fixture']['date'][11:16];home=found['teams']['home']['name'];away=found['teams']['away']['name'];ctry=found['league']['country'];league=found['league']['name'];dc=get_double_chance(fid) or "1X";time.sleep(0.5);sel.append(f"{ora} {home} vs {away} -> {dc} ({ctry} - {league})")
        if len(sel)>=33: break
    if not sel: tg('Oggi nessuna TOP LEAGUE',cid,reply=TAST_MAIN);return
    tg(f"BOLLA EUROPA {len(sel)} NAZIONI\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,reply=TAST_MAIN)
def run_corner(cid=None):
    tg('CORNER in arrivo...',cid,reply=TAST_MAIN)
def run_high_live_manual(cid=None):
    tg('LIVE @3+ controllo solo EUROPA 33...',cid,reply=TAST_MAIN)
def run_doppia(cid=None):
    tg('DOPPIA in arrivo...',cid,reply=TAST_MAIN)
def run_esatti(cid=None):
    tg('ESATTI in arrivo...',cid,reply=TAST_MAIN)
def poll():
    global is_paused,last_id
    try:
        if BOT: requests.get(f'https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true',timeout=10)
    except: pass
    while True:
        try:
            if not BOT: time.sleep(60);continue
            base=f'https://api.telegram.org/bot{BOT}';url=base+f'/getUpdates?offset={last_id+1}&timeout=20'
            r=requests.get(url,timeout=30).json()
            if r.get('ok'):
                for u in r.get('result',[]):
                    last_id=u['update_id']
                    msg=u.get('message',{});txt=(msg.get('text') or '').strip();low=txt.lower();cid=msg.get('chat',{}).get('id')
                    if not txt: continue
                    if txt.upper() in TOP_LEAGUES: tg(f"{txt.upper()} TOP LEAGUE OK",cid,reply=TAST_MAIN);continue
                    if 'CAMPIONATI' in txt.upper(): tg('SCEGLI NAZIONE (solo TOP EUROPA):',cid,reply=TAST_NAZIONI);continue
                    if 'MENU' in txt.upper() or '/start' in low: is_paused=False;tg('BOT V33.32 FIX JAPAN OK\nSolo EUROPA 33\nTastiera fissa\nPT 3 tiri + GIOCALO 6 tiri 70 + GOAL',cid,reply=TAST_MAIN);continue
                    if 'CORNER' in txt.upper(): run_corner(cid);continue
                    if 'LIVE' in txt.upper(): run_high_live_manual(cid);continue
                    if 'BOLLA' in txt.upper(): run_bolla(cid);continue
                    if 'DOPPIA' in txt.upper(): run_doppia(cid);continue
                    if 'ESATTI' in txt.upper(): run_esatti(cid);continue
                    if 'INDIETRO' in txt.upper(): tg('MENU:',cid,reply=TAST_MAIN);continue
                    if 'STATUS' in txt.upper(): tg('STATUS V33.32 OK - Solo EUROPA',cid,reply=TAST_MAIN);continue
                    if 'SPEGNI' in txt.upper(): is_paused=True;tg('PAUSA',cid,reply=TAST_MAIN);continue
                    if 'ACCENDI' in txt.upper(): is_paused=False;tg('ATTIVO',cid,reply=TAST_MAIN);continue
        except: pass
        time.sleep(1)
def live_loop():
    global last_bolla_hour,sot_sent,gol_tracker,gol_fatto,av_s_first,high_sent
    time.sleep(2)
    tg('BOT V33.32 ATTIVO - Solo 33 NAZIONI EUROPA - Japan filtrato!',reply=TAST_MAIN)
    while True:
        try:
            if is_paused: time.sleep(30);continue
            now=datetime.now(ITALY)
            if 0<=now.hour<7: time.sleep(300);continue
            if now.hour==7 and now.minute<5: sot_sent.clear();gol_tracker.clear();gol_fatto.clear();av_s_first.clear();high_sent.clear()
            games=api('https://v3.football.api-sports.io/fixtures?live=all')
            if games=='LIMIT': time.sleep(3600);continue
            if not games: time.sleep(60);continue
            for g in games:
                try:
                    if not is_top_match(g): continue
                    fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
                    if m is None: continue
                    home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'] or 0;ga=g['goals']['away'] or 0;tot=gh+ga
                    st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0
                    if st and len(st)>=2:
                        for s in st:
                            for x in s['statistics']:
                                if x['type']=='Shots on Goal':
                                    try: sot+=int(str(x['value'] or 0) or 0)
                                    except: pass
                    if tot>sot and sot>0: continue
                    ctry=g['league']['country'];league=g['league']['name']
                    if fid not in av_s_first and m<=45 and sot>=3: tg(f"PRIMO TEMPO {home} {gh}-{ga} {away} - {sot} TIRI\n{ctry} - {league}",reply=TAST_MAIN);av_s_first.add(fid)
                    if fid not in sot_sent and m<=70 and sot>=6: tg(f"GIOCALO! {home} {gh}-{ga} {away} - {sot} TIRI al {m}'\n{ctry} - {league}",reply=TAST_MAIN);sot_sent.add(fid);gol_tracker[fid]=tot
                    if fid in sot_sent and fid not in gol_fatto and tot>gol_tracker.get(fid,0): tg(f"GOAL! {home} {gh}-{ga} {away} - HA SEGNATO!\n{ctry} - {league} - {sot} TIRI al {m}'",reply=TAST_MAIN);gol_fatto.add(fid)
                except: continue
            time.sleep(45)
        except Exception as e:
            print(e);time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
