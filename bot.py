import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;av_g={};av_s=set();av_s_first=set();last_bolla_hour=-1;last_doppia_hour=-1
LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}
TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}
EUROPA_33=list(TOP_LEAGUES.keys())

def is_youth_league(name):
    n=name.lower()
    bad=['u19','u21','u23','u17','women',' w ','female','youth','reserve','development','academy',' u18',' u20']
    return any(x in n for x in bad)

app=Flask(__name__)
@app.route('/')
def home():return f'BOT V31 CLEAN - {datetime.now(ITALY).strftime("%H:%M")}',200
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True})

def tg(m,cid=None,keys=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT:return
  base=f'https://api.telegram.org/bot{BOT}';pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys:pay['reply_markup']=json.loads(TAST)
  requests.post(base+'/sendMessage',json=pay,timeout=25)
 except:pass

def api(url):
 try:
  r=requests.get(url,headers={'x-apisports-key':KEY},timeout=30)
  if r.status_code==429:return 'LIMIT'
  return r.json().get('response',[])
 except:return []

def get_double_chance(fid):
 try:
  data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
  if not data or data=='LIMIT':return None
  for book in data[0].get('bookmakers',[])[:3]:
   for bet in book.get('bets',[]):
    if 'Double Chance' in bet['name']:
     best=None;best_odd=10
     for v in bet['values']:
      try:
       odd=float(v['odd'])
       if odd<best_odd:best_odd=odd;best=v['value']
      except:continue
     if best:
      if 'Home/Draw' in best:return f"1X @ {best_odd}"
      if 'Draw/Away' in best:return f"X2 @ {best_odd}"
      if 'Home/Away' in best:return f"12 @ {best_odd}"
 except:pass
 return None

def get_over_15(fid):
 try:
  data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
  if not data or data=='LIMIT':return None
  for book in data[0].get('bookmakers',[])[:3]:
   for bet in book.get('bets',[]):
    if 'Goals Over/Under' in bet['name'] or 'Over/Under' in bet['name']:
     for v in bet['values']:
      if 'Over 1.5' in v['value']:
       try:return float(v['odd'])
       except:continue
 except:pass
 return None

def media(league_id,name):
 txt=name.upper()+"\n"+datetime.now(ITALY).strftime("%d/%m %H:%M")+"\n\n"
 teams=api(f'https://v3.football.api-sports.io/teams?league={league_id}&season=2024')
 if not teams:return 'Errore API'
 for t in teams[:14]:
  tid=t['team']['id'];tname=t['team']['name']
  last=api(f'https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024')
  if not last or last=='LIMIT':time.sleep(0.5);continue
  tot=0;c=0
  for p in last:
   gh=p['goals']['home'];ga=p['goals']['away']
   if gh is None:continue
   tot+=gh+ga;c+=1
  if c==0:continue
  med=tot/c
  txt+=("PIU DI 2" if med>2 else "MENO DI 2")+" - "+tname+": {:.2f}\n".format(med)
  time.sleep(0.4)
 return txt

def get_fixtures_today():
 today=datetime.now(ROME).strftime('%Y-%m-%d')
 return api(f'https://v3.football.api-sports.io/fixtures?date={today}&timezone=Europe/Rome')

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=='LIMIT':
  if not auto:tg('BOLLA: Limite API',cid,True)
  return
 sel=[]
 if not auto:tg('⏳ Cerco SOLO TOP LEAGUE + DOPPIA PIU ALTA... 30 sec',cid,True)
 for country,top_id in TOP_LEAGUES.items():
  found=None
  for f in data:
   if f['league']['id']==top_id and f['league']['country']==country:
    if is_youth_league(f['league']['name']):continue
    if f['fixture']['status']['short']!='NS':continue
    found=f
    break
  if not found:continue
  fid=found['fixture']['id'];ora=found['fixture']['date'][11:16];home=found['teams']['home']['name'];away=found['teams']['away']['name'];league=found['league']['name']
  dc=get_double_chance(fid)
  if not dc:dc="1X (no quota)"
  else:time.sleep(0.6)
  sel.append(f"{ora} {home} vs {away} -> {dc} ({league} - {country})")
  if len(sel)>=33:break
 if not sel:
  if not auto:tg('Oggi nessuna TOP LEAGUE in programma (pre-match)',cid,True)
  return
 pref=f"🌍 BOLLA EUROPA {len(sel)} NAZIONI - SOLO TOP LEAGUE - DOPPIA PIU ALTA PRE-MATCH\n\n" if auto else f"🌍 BOLLA EUROPA {len(sel)} NAZIONI - SOLO TOP LEAGUE - DOPPIA PIU ALTA PRE-MATCH\n\n"
 tg(pref+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=='LIMIT':
        if not auto:tg('DOPPIA: Limite API',cid,True)
        return
    out=[]
    if not auto:tg('⏳ Cerco OVER 1.5 PIU SICURI PRE-MATCH... 30 sec',cid,True)
    for f in data:
        try:
            if f['league']['country'] not in EUROPA_33:continue
            if is_youth_league(f['league']['name']):continue
            if f['fixture']['status']['short']!='NS':continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']):continue
            fid=f['fixture']['id']
            over_odd=get_over_15(fid)
            if over_odd is None:continue
            if over_odd>1.55:continue
            ora=f['fixture']['date'][11:16];home=f['teams']['home']['name'];away=f['teams']['away']['name'];league=f['league']['name']
            out.append(f"{ora} {home} vs {away} -> OVER
