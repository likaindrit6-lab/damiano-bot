import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g={};av_s=set();pre=set();pre1=set();cache={};tripla_coda=[];ultimo_invio_tripla=time.time()

LEAGUES={"Serie A":135,"Serie B":136,"Serie C":138,"Inghilterra":39,"Spagna":140,"Olanda":88,"Portogallo":94,"Belgio":144,"Francia":61,"Austria":218,"Danimarca":119,"Svizzera":207}

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT OK - {s} - {datetime.now(ITALY).strftime('%H:%M')}",200

TASTIERA_JSON=json.dumps({"keyboard":[["Serie A","Serie B","Serie C"],["Inghilterra","Spagna","Olanda"],["Portogallo","Belgio","Francia"],["Austria","Danimarca","Svizzera"],["TUTTA EUROPA","BOLLA EUROPA"],["ACCENDI","SPEGNI","STATUS"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        if not BOT_TOKEN or not cid: return
        base=f"https://api.telegram.org/bot{BOT_TOKEN}"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA_JSON
        requests.post(base+"/sendMessage",json=payload,timeout=25)
    except: pass

def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def media_gol_lega(league_id, nome_lega):
    try:
        txt=f"{nome_lega.upper()} - MEDIA GOL ULTIME 10\n{datetime.now(ITALY).strftime('%d/%m %H:%M')}\n\n"
        teams_resp=api_get(f"https://v3.football.api-sports.io/teams?league={league_id}&season=2024")
        if not teams_resp or teams_resp=="LIMIT": return f"Errore API {nome_lega}"
        for t in teams_resp[:16]:
            team_id=t['team']['id']; team_name=t['team']['name']
            last=api_get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&season=2024")
            if not last or last=="LIMIT": time.sleep(0.5); continue
            tot=0;c=0
            for p in last:
                gh=p['goals']['home']; ga=p['goals']['away']
                if gh is None: continue
                tot+=gh+ga; c+=1
            if c==0: continue
            media=tot/c
            icon="HOT" if media>2.5 else "LOW"
            txt+=f"{icon} {team_name} Media:{media:.2f}\n"
            time.sleep(0.35)
        return txt
    except Exception as e: return f"Errore {nome_lega}: {e}"

def crea_bolla():
    try:
        picks=[]; quota=1.0
        for gg in range(2):
            if len(picks)>=20: break
            giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
            fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
            if not fixtures: continue
            for p in fixtures:
                if len(picks)>=20: break
                if p['league']['id'] not in LEAGUES.values(): continue
                fid=p["fixture
