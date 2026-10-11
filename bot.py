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
EUROPA_33=list(TOP_LEAGUES.keys())
def is_youth_league(name):
    if not name: return False
    n=name.lower()
    bad=['u19','u21','u23','u17','u18','u20','women',' w','female','youth','reserve','academy','world']
    if n.strip().endswith(' w'): return True
    return any(x in n for x in bad)
app=Flask(__name__)
@app.route('/')
def home(): return f'BOT V33.31 TASTIERA FISSA - {datetime.now(ITALY).strftime("%H:%M")}',200
TAST_MAIN=json.dumps({"keyboard":[[{"text":"CAMPIONATI"}],[{"text":"CORNER"},{"text":"LIVE @3+"}],[{"text":"DOPPIA"},{"text":"BOLLA 33"}],[{"text":"ESATTI"}],[{"text":"STATUS"},{"text":"SPEGNI"},{"text":"ACCENDI"}]],"resize_keyboard":True,"is_persistent":True})
TAST_NAZIONI=json.dumps({"keyboard":[[{"text":"ITALY"},{"text":"ENGLAND"},{"text":"SPAIN"}],[{"text":"GERMANY"},{"text":"FRANCE"},{"text":"NETHERLANDS"}],[{"text":"PORTUGAL"},{"text":"BELGIUM"},{"text":"TURKEY"}],[{"text":"SCOTLAND"},{"text":"AUSTRIA"},{"text":"SWITZERLAND"}],[{"text":"DENMARK"},{"text":"SWEDEN"},{"text":"NORWAY"}],[{"text":"INDIETRO"},{"text":"MENU"}]],"resize_keyboard":True,"is_persistent":True})
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
def get_over_15(fid):
    try:
        data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
        if not data or data=='LIMIT': return None
        for book in data[0].get('bookmakers',[])[:3]:
            for bet in book.get('bets',[]):
                if 'Over/Under' in bet['name']:
                    for v in bet['values']:
                        if 'Over 1.5' in v['value']:
                            try: return float(v['odd'])
                            except: continue
    except: pass
    return None
def get_high_odd_live(fid):
    try:
        data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
        if not data or data=='LIMIT': return None
        for book in data[0].get('bookmakers',[])[:4]:
            for bet in book.get('bets',[]):
                bname=bet['name'].lower()
                if 'next goal' in bname or 'over/under' in bname or 'match winner' in bname:
                    for v in bet['values']:
                        try:
                            odd=float(v['odd'])
                            if odd>=3.0: return f"{bet['name']} {v['value']} @ {odd}"
                        except: continue
    except: pass
    return None
def get_correct_scores(fid):
    try:
        data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
        if not data or data=='LIMIT': return []
        scores=[]
        for book in data[0].get('bookmakers',[])[:2]:
            for bet in book.get('bets',[]):
                if 'Correct Score' in bet['name']:
                    for v in bet['values']:
                        try: scores.append((v['value'], float(v['odd'])))
                        except: continue
        scores=sorted(scores, key=lambda x: x[1]);seen=set();uniq=[]
        for s,o in scores:
            if s not in seen: seen.add(s);uniq.append(s)
            if len(uniq)>=5: break
        return uniq
    except: return []
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
def run_doppia(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('DOPPIA: Limite API',cid,reply=TAST_MAIN);return
    out=[]
    for f in data:
        try:
            if f['league']['country'] not in EUROPA_33: continue
            if is_youth_league(f['league']['name']): continue
            if f['fixture']['status']['short']!='NS': continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']): continue
            fid=f['fixture']['id'];over_odd=get_over_15(fid)
            if over_odd is None or over_odd>1.55: continue
            ora=f['fixture']['date'][11:16];home=f['teams']['home']['name'];away=f['teams']['away']['name'];ctry=f['league']['country'];league=f['league']['name'];out.append(f"{ora} {home} vs {away} -> OVER 1.5 @ {over_odd} ({ctry} - {league})");time.sleep(0.6)
            if len(out)>=15: break
        except: continue
    if not out: tg('Nessun OVER 1.5 <1.55 oggi',cid,reply=TAST_MAIN);return
    tg(f"DOPPIA ALTA % - {len(out)} OVER 1.5\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,reply=TAST_MAIN)
def run_corner(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('CORNER: Limite API',cid,reply=TAST_MAIN);return
    tg('Cerco CORNER OVER 7.5...',cid,reply=TAST_MAIN);out=[]
    for f in data:
        try:
            if f['league']['country'] not in EUROPA_33: continue
            if is_youth_league(f['league']['name']): continue
            if f['fixture']['status']['short']!='NS': continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']): continue
            fid=f['fixture']['id'];d=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
            if not d or d=='LIMIT': continue
            found=False
            for book in d[0].get('bookmakers',[])[:3]:
                for bet in book.get('bets',[]):
                    if 'corner' in bet['name'].lower():
                        for v in bet['values']:
                            if 'Over 7.5' in v['value']:
                                try:
                                    if float(v['odd'])<1.90: found=True
                                except: pass
            if found: ora=f['fixture']['date'][11:16];home=f['teams']['home']['name'];away=f['teams']['away']['name'];ctry=f['league']['country'];league=f['league']['name'];out.append(f"{ora} {home} vs {away} ({ctry} - {league})")
            time.sleep(0.6)
            if len(out)>=15: break
        except: continue
    if not out: tg('Nessun OVER 7.5 oggi',cid,reply=TAST_MAIN);return
    tg(f"CORNER 90% - {len(out)} PARTITE\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,reply=TAST_MAIN)
def run_high_live_manual(cid=None):
    games=api('https://v3.football.api-sports.io/fixtures?live=all')
    if not games or games=='LIMIT': tg('LIVE: Limite API',cid,reply=TAST_MAIN);return
    tg('Cerco LIVE 90% @3+...',cid,reply=TAST_MAIN);out=[]
    for g in games:
        try:
            if is_youth_league(g['league']['name']): continue
            fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
            if m is None or m<60: continue
            st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0
            if st and len(st)>=2:
                for s in st:
                    for x in s['statistics']:
                        if x['type']=='Shots on Goal':
                            try: sot+=int(str(x['value'] or 0) or 0)
                            except: pass
            if sot<6: continue
            high=get_high_odd_live(fid)
            if high: home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'] or 0;ga=g['goals']['away'] or 0;ctry=g['league']['country'];league=g['league']['name'];out.append(f"{home} {gh}-{ga} {away} - {sot} TIRI\n{high}\n{ctry} - {league}")
            time.sleep(0.8)
            if len(out)>=5: break
        except: continue
    if not out: tg('Nessun LIVE @3+ ora',cid,reply=TAST_MAIN);return
    tg(f"LIVE 90% @3+ - {len(out)} PARTITE\n\n"+'\n\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,reply=TAST_MAIN)
def run_esatti(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('ESATTI: Limite API',cid,reply=TAST_MAIN);return
    tg('Cerco ESATTI...',cid,reply=TAST_MAIN);sel=[]
    for f in data:
        try:
            if f['league']['country'] not in EUROPA_33: continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']): continue
            if is_youth_league(f['league']['name']): continue
            if f['fixture']['status']['short']!='NS': continue
            fid=f['fixture']['id'];scores=get_correct_scores(fid)
            if len(scores)<3: continue
            ora=f['fixture']['date'][11:16];home=f['teams']['home']['name'];away=f['teams']['away']['name'];ctry=f['league']['country'];league=f['league']['name'];txt_score=" - ".join(scores[:5]);sel.append(f"{ora} {home} vs {away} ({ctry} - {league})\n -> {txt_score}");time.sleep(0.8)
            if len(sel)>=10: break
        except: continue
    if not sel: tg('Nessun big match oggi',cid,reply=TAST_MAIN);return
    tg(f"MULTI ESATTI - {len(sel)} PARTITE\n\n" + "\n\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,reply=TAST_MAIN)
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
                    if txt.upper() in TOP_LEAGUES: tg(f"{txt.upper()} selezionata - TOP LEAGUE",cid,reply=TAST_MAIN);continue
                    if 'CAMPIONATI' in txt.upper(): tg('SCEGLI NAZIONE:',cid,reply=TAST_NAZIONI);continue
                    if 'MENU' in txt.upper() or '/start' in low: is_paused=False;tg('BOT V33.31 TASTIERA FISSA OK',cid,reply=TAST_MAIN);continue
                    if 'CORNER' in txt.upper(): run_corner(cid);continue
                    if 'LIVE' in txt.upper() or '/live' in low: run_high_live_manual(cid);continue
                    if 'BOLLA' in txt.upper(): run_bolla(cid);continue
                    if 'DOPPIA' in txt.upper(): run_doppia(cid);continue
                    if 'ESATTI' in txt.upper(): run_esatti(cid);continue
                    if 'INDIETRO' in txt.upper(): tg('MENU:',cid,reply=TAST_MAIN);continue
                    if 'STATUS' in txt.upper(): tg('STATUS V33.31 OK',cid,reply=TAST_MAIN);continue
                    if 'SPEGNI' in txt.upper() or '/pausa' in low: is_paused=True;tg('PAUSA',cid,reply=TAST_MAIN);continue
                    if 'ACCENDI' in txt.upper(): is_paused=False;tg('ATTIVO',cid,reply=TAST_MAIN);continue
        except: pass
        time.sleep(1)
def live_loop():
    global last_bolla_hour,sot_sent,gol_tracker,gol_fatto,av_s_first,high_sent
    tg('BOT V33.31 TASTIERA FISSA - NON SPARISCE PIU',reply=TAST_MAIN)
    while True:
        try:
            if is_paused: time.sleep(30);continue
            now=datetime.now(ITALY)
            if 0<=now.hour<7: time.sleep(300);continue
            if now.hour==7 and now.minute<5: sot_sent.clear();gol_tracker.clear();gol_fatto.clear();av_s_first.clear();high_sent.clear()
            if now.hour!=last_bolla_hour and now.minute<10:
                last_bolla_hour=now.hour
                games_hour=api('https://v3.football.api-sports.io/fixtures?live=all')
                if games_hour and games_hour!='LIMIT':
                    out=[]
                    for g in games_hour:
                        try:
                            if is_youth_league(g['league']['name']): continue
                            fid=g['fixture']['id']
                            if fid in high_sent: continue
                            m=g['fixture']['status']['elapsed']
                            if m is None or m<60: continue
                            st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0
                            if st and len(st)>=2:
                                for s in st:
                                    for x in s['statistics']:
                                        if x['type']=='Shots on Goal':
                                            try: sot+=int(str(x['value'] or 0) or 0)
                                            except: pass
                            if sot>=6:
                                high=get_high_odd_live(fid)
                                if high: home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'] or 0;ga=g['goals']['away'] or 0;ctry=g['league']['country'];league=g['league']['name'];out.append(f"{home} {gh}-{ga} {away} - {sot} TIRI\n{high}\n{ctry} - {league}");high_sent.add(fid)
                                if len(out)>=5: break
                            time.sleep(0.5)
                        except: continue
                    if out: tg(f"LIVE 90% @3+ - {len(out)} PARTITE\n\n"+'\n\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),reply=TAST_MAIN)
            games=api('https://v3.football.api-sports.io/fixtures?live=all')
            if games=='LIMIT': time.sleep(3600);continue
            if not games: time.sleep(60);continue
            for g in games:
                try:
                    if is_youth_league(g['league']['name']): continue
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
