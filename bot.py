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
last_bolla_hour=-1

LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}

TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}

EUROPA_33=list(TOP_LEAGUES.keys())

def is_youth_league(name):
    n=name.lower()
    bad=['u19','u21','u23','women','youth','reserve']
    return any(x in n for x in bad)

app=Flask(__name__)

@app.route('/')
def home():
    return f'BOT V36 FIXED - {datetime.now(ROME).strftime("%H:%M")}',200

TAST=json.dumps({
    "keyboard":[
        ["Serie A","Serie B","Inghilterra"],
        ["Spagna","Germania","Francia"],
        ["Olanda","Portogallo","Turchia"],
        ["DOPPIA 90%"],
        ["BOLLA EUROPA 33 NAZIONI"],
        ["STATUS"],
        ["ACCENDI","SPEGNI"]
    ],
    "resize_keyboard":True
})

def tg(m,cid=None,keys=False):
    try:
        cid=cid or CHAT
        if not cid or not BOT:
            return
        base=f'https://api.telegram.org/bot{BOT}'
        pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if keys:
            pay['reply_markup']=json.loads(TAST)
        requests.post(base+'/sendMessage',json=pay,timeout=30)
    except:
        pass

def api(url):
    try:
        r=requests.get(url,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429:
            return 'LIMIT'
        return r.json().get('response',[])
    except:
        return []

def get_double_chance_90(fid):
    try:
        data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
        if not data or data=='LIMIT':
            return None
        if len(data)==0:
            return None
        for book in data[0].get('bookmakers',[])[:3]:
            for bet in book.get('bets',[]):
                if 'Double Chance' in bet['name']:
                    best=None
                    best_odd=100
                    for v in bet['values']:
                        try:
                            odd=float(v['odd'])
                            if odd<best_odd:
                                best_odd=odd
                                best=v['value']
                        except:
                            continue
                    if best:
                        prob=(1/best_odd*100)
                        if 'Home/Draw' in best:
                            return f"1X @ {best_odd:.2f} ({prob:.0f}%)",prob
                        if 'Draw/Away' in best:
                            return f"X2 @ {best_odd:.2f} ({prob:.0f}%)",prob
                        if 'Home/Away' in best:
                            return f"12 @ {best_odd:.2f} ({prob:.0f}%)",prob
    except:
        pass
    return None

def media(league_id,name):
    txt=f"<b>{name.upper()} - 10 ULTIME</b>\n{datetime.now(ROME).strftime('%d/%m %H:%M')} Italia\n\n"
    teams=api(f'https://v3.football.api-sports.io/teams?league={league_id}&season=2024')
    if not teams:
        return 'Errore API'
    for t in teams[:14]:
        tid=t['team']['id']
        tname=t['team']['name']
        last=api(f'https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024')
        if not last:
            continue
        if last=='LIMIT':
            time.sleep(0.6)
            continue
        gf=0
        gs=0
        tot=0
        c=0
        over=0
        for p in last:
            gh=p['goals']['home']
            ga=p['goals']['away']
            if gh is None:
                continue
            is_home=p['teams']['home']['id']==tid
            if is_home:
                gf+=gh
                gs+=ga
            else:
                gf+=ga
                gs+=gh
            tot+=gh+ga
            c+=1
            if gh+ga>=2:
                over+=1
        if c==0:
            continue
        med=tot/c
        diff=gf-gs
        perc=int(over/c*100)
        if perc>=70:
            col="🟢"
        elif perc>=50:
            col="🟡"
        else:
            col="🔴"
        txt+=f"{col} {tname}: {gf}F/{gs}S Diff {diff:+} | {med:.2f} | Over1.5 {perc}%\n"
        time.sleep(0.4)
    return txt

def get_fixtures_today():
    today=datetime.now(ROME).strftime('%Y-%m-%d')
    return api(f'https://v3.football.api-sports.io/fixtures?date={today}&timezone=Europe/Rome')

def run_bolla(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=='LIMIT':
        if not auto:
            tg('BOLLA: Limite API',cid,True)
        return
    sel=[]
    if not auto:
        tg('⏳ BOLLA 33 in corso...',cid,True)
    for country,top_id in TOP_LEAGUES.items():
        found=None
        for f in data:
            if f['league']['id']==top_id and f['league']['country']==country:
                if is_youth_league(f['league']['name']):
                    continue
                if f['fixture']['status']['short']!='NS':
                    continue
                found=f
                break
        if not found:
            continue
        fid=found['fixture']['id']
        ora=found['fixture']['date'][11:16]
        home=found['teams']['home']['name']
        away=found['teams']['away']['name']
        league=found['league']['name']
        res=get_double_chance_90(fid)
        if res:
            dc=res[0]
            time.sleep(0.6)
        else:
            dc="1X"
        sel.append(f"{ora} {home} vs {away} -> {dc} ({league})")
        if len(sel)>=33:
            break
    if not sel:
        if not auto:
            tg('Nessuna partita oggi',cid,True)
        return
