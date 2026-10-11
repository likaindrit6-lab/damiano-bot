import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;last_bolla_hour=-1
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
def home(): return f'BOT V33.17 FIX OK - {datetime.now(ITALY).strftime("%H:%M")}',200
TAST_MAIN=json.dumps({"inline_keyboard":[
    [{"text":"📋 CAMPIONATI","callback_data":"open_leagues"}],
    [{"text":"🚩 CORNER","callback_data":"corner"},{"text":"🔥 LIVE 90% @3+","callback_data":"high"}],
    [{"text":"💎 DOPPIA","callback_data":"doppia"},{"text":"🌍 BOLLA 33","callback_data":"bolla"}],
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
                if 'next goal' in bname or 'over/under' in bname or 'match winner' in bname:
                    for v in bet['values']:
                        try:
                            odd=float(v['odd'])
                            if odd >= 3.0:
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
        fid=found['fixture']['id']; ora=found['fixture']['date'][11:16]; home=found['teams']['home']['name']; away=found['teams']['away']['name']; league=found['league']['name']
        dc=get_double_chance(fid) or "1X"; time.sleep(0.5)
        sel.append(f"{ora} {home} vs {away} -> {dc} ({league})")
        if len(sel)>=33: break
    if not sel: tg('Oggi nessuna TOP LEAGUE',cid); return
    tg(f"BOLLA {len(sel)} NAZIONI\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid)
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
    if not out: tg('Nessun OVER 1.5 oggi',cid); return
    tg(f"DOPPIA {len(out)} OVER 1.5\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid)
def run_corner(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT': tg('CORNER: Limite API',cid); return
    tg('Cerco CORNER...',cid)
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
                    if 'corner' in bet
