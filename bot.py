import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT=os.getenv('BOT_TOKEN')
CHAT=os.getenv('CHAT_ID')
KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_id=0
av_g={}
av_s=set()
pre=set()
pre1=set()
cache={}

LEAGUES={'Serie A':135,'Serie B':136,'Serie C':138,'Inghilterra':39,'Championship':40,'Spagna':140,'Spagna 2':142,'Germania':78,'Germania 2':79,'Francia':61,'Francia 2':62,'Olanda':88,'Portogallo':94,'Belgio':144,'Scozia':179,'Austria':218,'Svizzera':207,'Danimarca':119,'Svezia':113,'Norvegia':103,'Turchia':203,'Grecia':197,'Polonia':106,'Cechia':345,'Croazia':210,'Serbia':286,'Romania':283,'Ungheria':271,'Ucraina':333,'Russia':235,'Cipro':318,'Bulgaria':172,'Irlanda':344}

app=Flask(__name__)
@app.route('/')
def home():
    return f'BOT V22 FIX - {datetime.now(ITALY).strftime("%H:%M")}',200

TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["MODELLO AMERICANO 33"],["BOLLA 20","STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True,"is_persistent":False,"one_time_keyboard":True})

def tg(m,cid=None,keys=False):
    try:
        cid=cid or CHAT
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
        return r.json().get('response',[])
    except:
        return []

def media(lid,name):
    txt=f"{name.upper()} - MEDIA ULTIME 10\n{datetime.now(ITALY).strftime('%d/%m %H:%M')}\n\n"
    teams=api(f"https://v3.football.api-sports.io/teams?league={lid}&season=2024")
    if not teams:
        return "Errore API"
    for t in teams[:14]:
        try:
            tid=t['team']['id']
            tname=t['team']['name']
            last=api(f"https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024")
            if not last or last=='LIMIT':
                time.sleep(0.5)
                continue
            tot=0
            c=0
            for p in last:
                gh=p['goals']['home']
                if gh is None:
                    continue
                tot+=p['goals']['home']+p['goals']['away']
                c+=1
            if c==0:
                continue
            med=tot/c
            et="PIU DI 2" if med>2 else "MENO DI 2"
            txt+=f"{et} - {tname}: {med:.2f}\n"
            time.sleep(0.4)
        except:
            continue
    return txt

def crea_doppia():
    try:
        txt=f"DOPPIA ALTA % - 33 NAZIONI\n{datetime.now(ITALY).strftime('%d/%m')}\n\n"
        ris=[]
        BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly"]
        for gg in range(7):
            giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
            fixtures=api(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
            if not fixtures or fixtures=='LIMIT':
                continue
            for p in fixtures:
                if p['league']['id'] not in LEAGUES.values():
                    continue
                if any(b.lower() in p["league"]["name"].lower() for b in BAN):
                    continue
                dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
                if dt < datetime.now(
