import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;last_bolla_hour=-1
sot_sent=set();gol_tracker={};gol_fatto=set();av_s_first=set();high_sent=set()
TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}
EUROPA_33=list(TOP_LEAGUES.keys())
def is_youth_league(name):
    if not name: return False
    n=name.lower()
    bad=['u19','u21','u23','u17','u18','u20','women',' w','female','ladies','girls','youth','reserve','academy','world']
    if n.strip().endswith(' w'): return True
    return any(x in n for x in bad)
app=Flask(__name__)
@app.route('/')
def home(): return f'BOT V33.10 FULL - {datetime.now(ITALY).strftime("%H:%M")}',200
TAST_MAIN=json.dumps({"inline_keyboard":[
    [{"text":"📋 CAMPIONATI - 33 NAZIONI","callback_data":"open_leagues"}],
    [{"text":"🚩 CORNER 90% (SOLO RICHIESTA)","callback_data":"corner"},{"text":"🔥 LIVE 90% @3+","callback_data":"high"}],
    [{"text":"💎 DOPPIA ALTA %","callback_data":"doppia"},{"text":"🌍 BOLLA 33","callback_data":"bolla"}],
    [{"text":"🎯 ESATTI","callback_data":"esatti"}],
    [{"text":"📊 STATUS","callback_data":"status"},{"text":"⏸️ SPEGNI","callback_data":"spegni"},{"text":"▶️ ACCENDI","callback_data":"accendi"}]
]})
REMOVE_OLD=json.dumps({"remove_keyboard":True})
def build_leagues_keyboard(page=1):
    keys=list(TOP_LEAGUES.keys()); per_page=18; start=(page-1)*per_page; end=start+per_page; chunk=keys[start:end]
    kb=[]; row=[]
    for k in chunk:
        row.append({"text":k.upper()[:12],"callback_data":f"league_{k}"})
        if len(row)==3: kb.append(row); row=[]
    if row: kb.append(row)
    nav=[]
    if page>1: nav.append({"text":"⬅️ INDIETRO","callback_data":f"page_{page-1}"})
    if end < len(keys): nav.append({"text":"AVANTI ➡️","callback_data":f"page_{page+1}"})
    nav.append({"text":"❌ CHIUDI","callback_data":"back_main"}); kb.append(nav)
    return json.dumps({"inline_keyboard":kb})
def tg(m,cid=None,inline=None,remove=False):
    try:
        cid=cid or CHAT
        if not cid or not BOT: return
        base=f'https://api.telegram.org/bot{BOT}'; pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if remove: pay['reply_markup']=json.loads(REMOVE_OLD)
        elif inline: pay['reply_markup']=json.loads(inline) if isinstance(inline,str) else inline
        requests.post(base+'/sendMessage',json=pay,timeout=25)
    except: pass
def tg_edit(mid,cid,text,inline):
    try:
        base=f'https://api.telegram.org/bot{BOT}'
        pay={'chat_id':cid,'message_id':mid,'text':text,'parse_mode':'HTML','reply_markup':json.loads(inline) if isinstance(inline,str) else inline}
        requests.post(base+'/editMessageText',json=pay,timeout=25)
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
                    best=None; best_odd=10
                    for v in bet['values']:
                        try:
                            odd=float(v['odd'])
                            if odd<best_odd: best_odd=odd; best=v['value']
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
                if 'next goal' in bname or 'over/under' in bname or 'goals over/under' in bname or 'match winner' in bname:
                    for v in bet['values']:
                        try:
                            odd=float(v['odd'])
                            if 3.0 <= odd <= 4.2:
                                return f"{bet['name']} {v['value']} @ {odd}"
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
        scores=sorted(scores, key=lambda x: x[1])
        seen=set(); uniq=[]
        for s,o in scores:
            if s not in seen:
                seen.add(s); uniq.append(s)
            if len(uniq)>=5: break
        return uniq
    except: return []
def media(league_id,name):
    txt=name.upper()+"\n"+datetime.now(ITALY).strftime("%d/%m %H:%M")+"\n\n"
    teams=api(f'https://v3.football.api-sports.io/teams?league={league_id}&season=2024')
    if not teams: return 'Errore API'
    for t in teams[:14]:
        tid=t['team']['id']; tname=t['team']['name']
        last=api(f'https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024')
        if not last or last=='LIMIT': time.sleep(0.5); continue
        tot=0; c=0
        for p in last:
            gh=p['goals']['home']; ga=p['goals']['away']
            if gh is None: continue
            tot+=gh+ga; c+=1
        if c==0: continue
        txt+=("PIU DI 2" if tot/c>2 else "MENO DI 2")+f" - {tname}: {tot/c:.2f}\n"
        time.sleep(0.4)
    return txt
def get_fixtures_today():
    today=datetime.now(ROME).strftime('%Y-%m-%d')
    return api(f'https://v3.football.api-sports.io/fixtures?date={today}')
def run_bolla(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('BOLLA: Limite API',cid); return
    sel=[]
    for country,top_id in TOP_LEAGUES.items():
        found=None
        for f in data:
            if f['league']['id']==top_id and f['league']['country']==country:
                if is_youth_league(f['league']['name']): continue
                if f['fixture']['status']['short']!='NS': continue
                found=f; break
        if not found: continue
        fid=found['fixture']['id']
        ora=found['fixture']['date'][11:16]
        home=found['teams']['home']['name']
        away=found['teams']['away']['name']
        league=found['league']['name']
        dc=get_double_chance(fid) or "1X"
        time.sleep(0.5)
        sel.append(f"{ora} {home} vs {away} -> {dc} ({league})")
        if len(sel)>=33: break
    if not sel: tg('Oggi nessuna TOP LEAGUE',cid); return
    tg(f"BOLLA EUROPA {len(sel)} NAZIONI\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid)
def run_doppia(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('DOPPIA: Limite API',cid); return
    out=[]
    for f in data:
        try:
            if f['league']['country'] not in EUROPA_33: continue
            if is_youth_league(f['league']['name']): continue
            if f['fixture']['status']['short']!='NS': continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']): continue
            fid=f['fixture']['id']
            over_odd=get_over_15(fid)
            if over_odd is None or over_odd>1.55: continue
            ora=f['fixture']['date'][11:16]; home=f['teams']['home']['name']; away=f['teams']['away']['name']; league=f['league']['name']
            out.append(f"{ora} {home} vs {away} -> OVER 1.5 @ {over_odd} ({league})")
            time.sleep(0.6)
            if len(out)>=15: break
        except: continue
    if not out: tg('Nessun OVER 1.5 <1.55 oggi',cid); return
    tg(f"DOPPIA ALTA % - {len(out)} OVER 1.5\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid)
def run_corner(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('CORNER: Limite API',cid); return
    tg('Cerco CORNER OVER 7.5 SOLO SU RICHIESTA... 30 sec',cid)
    out=[]
    for f in data:
        try:
            if f['league']['country'] not in EUROPA_33: continue
            if is_youth_league(f['league']['name']): continue
            if f['fixture']['status']['short']!='NS': continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']): continue
            fid=f['fixture']['id']
            d=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
            if not d or d=='LIMIT': continue
            found=False
            for book in d[0].get('bookmakers',[])[:3]:
                for bet in book.get('bets',[]):
                    if 'corner' in bet['name'].lower():
                        for v in bet['values']:
                            if 'Over 7.5' in v['value']:
                                try:
                                    if float(v['odd']) < 1.90: found=True
                                except: pass
            if found:
                ora=f['fixture']['date'][11:16]; home=f['teams']['home']['name']; away=f['teams']['away']['name']; league=f['league']['name']
                out.append(f"{ora} {home} vs {away} ({league})")
            time.sleep(0.6)
            if len(out)>=15: break
        except: continue
    if not out: tg('Nessun OVER 7.5 oggi',cid); return
    tg(f"🚩 CORNER 90% - {len(out)} PARTITE - SOLO SU RICHIESTA\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid)
def run_high_live_manual(cid=None):
    games=api('https://v3.football.api-sports.io/fixtures?live=all')
    if not games or games=='LIMIT': tg('LIVE: Limite API o nessuna live',cid); return
    tg('Cerco LIVE 90% @3+... 30 sec',cid)
    out=[]
    for g in games:
        try:
            if g['league']['country'] not in EUROPA_33: continue
            if is_youth_league(g['league']['name']): continue
            fid=g['fixture']['id']; m=g['fixture']['status']['elapsed']
            if m is None or m < 55: continue
            st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
            sot=0
            if st and len(st)>=2:
                for s in st:
                    for x in s['statistics']:
                        if x['type']=='Shots on Goal':
                            try: sot+=int(str(x['value'] or 0) or 0)
                            except: pass
            if sot < 5: continue
            high=get_high_odd_live(fid)
            if high and ('3.' in high or '4.' in high):
                home=g['teams']['home']['name']; away=g['teams']['away']['name']; gh=g['goals']['home'] or 0; ga=g['goals']['away'] or 0
                out.append(f"{m}' {home} {gh}-{ga} {away} - {sot} TIRI\n{high}\n{g['league']['name']}")
            time.sleep(0.8)
            if len(out)>=10: break
        except: continue
    if not out: tg('Nessun LIVE @3+ in questo momento',cid); return
    tg(f"🔥 LIVE 90% QUOTA ALTA 3+ - {len(out)} PARTITE\n\n"+'\n\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid)
def run_esatti(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('ESATTI: Limite API',cid); return
    tg('Cerco 5 RISULTATI... 40 sec',cid)
    sel=[]
    for f in data:
        try:
            if f['league']['country'] not in EUROPA_33: continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']): continue
            if is_youth_league(f['league']['name']): continue
            if f['fixture']['status']['short']!='NS': continue
            fid=f['fixture']['id']
            scores=get_correct_scores(fid)
            if len(scores)<3: continue
            ora=f['fixture']['date'][11:16]; home=f['teams']['home']['name']; away=f['teams']['away']['name']; league=f['league']['name']
            txt_score=" - ".join(scores[:5])
            sel.append(f"{ora} {home} vs {away} ({league})\n -> {txt_score}")
            time.sleep(0.8)
            if len(sel)>=10: break
        except: continue
    if not sel: tg('Nessun big match oggi',cid); return
    tg(f"MULTI ESATTI - {len(sel)} PARTITE\n\n" + "\n\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid)
def poll():
    global is_paused,last_id
    try:
        if BOT: requests.get(f'https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true',timeout=10)
    except: pass
    while True:
        try:
            if not BOT: time.sleep(60); continue
            base=f'https://api.telegram.org/bot{BOT}'; url=base+f'/getUpdates?offset={last_id+1}&timeout=20'
            r=requests.get(url,timeout=30).json()
            if r.get('ok'):
                for u in r.get('result',[]):
                    last_id=u['update_id']
                    cb=u.get('callback_query')
                    if cb:
                        cid=cb['message']['chat']['id']; mid=cb['message']['message_id']; data=cb.get('data','')
                        try: requests.post(base+'/answerCallbackQuery',json={'callback_query_id':cb['id']},timeout=10)
                        except: pass
                        if data=='open_leagues': tg_edit(mid,cid,"📋 SCEGLI NAZIONE:",build_leagues_keyboard(1))
                        elif data.startswith('page_'):
                            p=int(data.split('_')[1]); tg_edit(mid,cid,f"📋 PAGINA {p}:",build_leagues_keyboard(p))
                        elif data=='back_main': tg_edit(mid,cid,"✅ BOT V33.10 FULL",TAST_MAIN)
                        elif data.startswith('league_'):
                            country=data.replace('league_',''); lid=TOP_LEAGUES.get(country)
                            if lid: tg(media(lid,country),cid)
                        elif data=='corner': run_corner(cid)
                        elif data=='high': run_high_live_manual(cid)
                        elif data=='bolla': run_bolla(cid)
                        elif data=='doppia': run_doppia(cid)
                        elif data=='esatti': run_esatti(cid)
                        elif 'spegni' in data: is_paused=True; tg('⏸️ PAUSA',cid)
                        elif 'accendi' in data: is_paused=False; tg('▶️ V33.10 FULL ATTIVO',cid,inline=TAST_MAIN)
                        elif 'status' in data: tg('STATUS V33.10 FULL: TUTTO DENTRO - LIVE 90% @3+ OGNI ORA',cid)
                        continue
                    msg=u.get('message',{}); txt=(msg.get('text') or '').strip(); low=txt.lower(); cid=msg.get('chat',{}).get('id')
                    if not txt: continue
                    if '/start' in low:
                        is_paused=False
                        tg('Pulisco vecchia tastiera...',cid,remove=True)
                        time.sleep(1)
                        tg('✅ BOT V33.10 FULL - TUTTO DENTRO\n🔥 LIVE 90% @3+ OGNI ORA\n✅ SOT 5 LIVE\n📋 Clicca sotto',cid,inline=TAST_MAIN)
        except: pass
        time.sleep(1)
def live_loop():
    global last_bolla_hour,sot_sent,gol_tracker,gol_fatto,av_s_first,high_sent
    tg('Pulisco...',remove=True); time.sleep(1)
    tg('✅ BOT V33.10 FULL ATTIVO - LIVE 90% @3+ OGNI ORA',inline=TAST_MAIN)
    while True:
        try:
            if is_paused: time.sleep(30); continue
            now=datetime.now(ITALY)
            if 2<=now.hour<6: time.sleep(300); continue
            if now.hour!=last_bolla_hour and now.minute<10:
                last_bolla_hour=now.hour
                games_hour=api('https://v3.football.api-sports.io/fixtures?live=all')
                if games_hour and games_hour!='LIMIT':
                    for g in games_hour:
                        try:
                            if g['league']['country'] not in EUROPA_33: continue
                            if is_youth_league(g['league']['name']): continue
                            fid=g['fixture']['id']
                            if fid in high_sent: continue
                            m=g['fixture']['status']['elapsed']
                            if m is None or m < 60: continue
                            st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
                            sot=0
                            if st and len(st)>=2:
                                for s in st:
                                    for x in s['statistics']:
                                        if x['type']=='Shots on Goal':
                                            try: sot+=int(str(x['value'] or 0) or 0)
                                            except: pass
                            if sot >= 6:
                                high=get_high_odd_live(fid)
                                if high and ('3.' in high or '4.' in high):
                                    home=g['teams']['home']['name']; away=g['teams']['away']['name']
                                    gh=g['goals']['home'] or 0; ga=g['goals']['away'] or 0
                                    tg(f"🔥 LIVE 90% @3+ {m}' {home} {gh}-{ga} {away}\n{sot} TIRI - {high}\n{g['league']['name']}")
                                    high_sent.add(fid)
                                    time.sleep(1)
                        except: continue
            games=api('https://v3.football.api-sports.io/fixtures?live=all')
            if games=='LIMIT': time.sleep(3600); continue
            if not games: time.sleep(60); continue
            for g in games:
                try:
                    if g['league']['country'] not in EUROPA_33: continue
                    if is_youth_league(g['league']['name']): continue
                    fid=g['fixture']['id']; m=g['fixture']['status']['elapsed']
                    if m is None: continue
                    home=g['teams']['home']['name']; away=g['teams']['away']['name']
                    gh=g['goals']['home'] or 0; ga=g['goals']['away'] or 0; tot_gol=gh+ga
                    st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
                    sot=0
                    if st and len(st)>=2:
                        for s in st:
                            for x in s['statistics']:
                                if x['type']=='Shots on Goal':
                                    try: sot+=int(str(x['value'] or 0) or 0)
                                    except: pass
                    if tot_gol > sot and sot>0: continue
                    if 30<=m<=45 and fid not in av_s_first and sot>=3:
                        tg(f"🔥 PRIMO TEMPO {m}' {home} {gh}-{ga} {away} Tiri:{sot}"); av_s_first.add(fid)
                    if m < 70 and fid not in sot_sent and sot >= 5:
                        tg(f"🚀 GIOCALO {m}' {home} {gh}-{ga} {away} - {sot} TIRI SOTTO 70\n{g['league']['name']}")
                        sot_sent.add(fid); gol_tracker[fid]=tot_gol
                    if fid in sot_sent and fid not in gol_fatto:
                        if tot_gol > gol_tracker.get(fid,0):
                            tg(f"⚽ GOAL VINTO! {m}' {home} {gh}-{ga} {away} - Era {sot} tiri"); gol_fatto.add(fid)
                except: continue
            time.sleep(45)
        except Exception as e:
            print(e); time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
