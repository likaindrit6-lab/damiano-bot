import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;av_g={};av_s=set();av_s_first=set();last_bolla_hour=-1
LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}
# ID CORRETTI TOP LEAGUE - FIX POLAND ECC
TOP_LEAGUES={
'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,
'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':106,'Czech Republic':345,
'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,
'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116
}
# Se top non c'è, usa anche seconde leghe per riempire bolla
SECOND_LEAGUES={'Poland':107,'England':40,'Italy':136,'Spain':141,'Germany':79,'France':62,'Belarus':117,'Scotland':180}
EUROPA_33=list(TOP_LEAGUES.keys())

def is_youth_league(name):
    n=name.lower()
    return any(x in n for x in ['u19','u21','u23','u17','women',' w ','female','youth','reserve','academy'])

app=Flask(__name__)
@app.route('/')
def home():return f'BOT V39 - {datetime.now(ROME).strftime("%H:%M")}',200
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA 90%"],["BOLLA EUROPA 33 NAZIONI"],["STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True})

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
  if not data or data=='LIMIT' or len(data)==0:return None
  for book in data[0].get('bookmakers',[])[:4]:
   for bet in book.get('bets',[]):
    if 'Double Chance' in bet['name']:
     best=None;best_odd=10
     for v in bet['values']:
      try:
       odd=float(v['odd'])
       if odd<best_odd:best_odd=odd;best=v['value']
      except:continue
     if best:
      prob=int(100/float(best_odd)) if best_odd else 0
      if 'Home/Draw' in best:return f"1X @ {best_odd} ({prob}%)"
      if 'Draw/Away' in best:return f"X2 @ {best_odd} ({prob}%)"
      if 'Home/Away' in best:return f"12 @ {best_odd} ({prob}%)"
 except:pass
 return None

def get_fixtures_day(day_str):
    return api(f'https://v3.football.api-sports.io/fixtures?date={day_str}&timezone=Europe/Rome')

def run_bolla(cid=None,auto=False):
    try:
        today = datetime.now(ROME).strftime('%Y-%m-%d')
        tomorrow = (datetime.now(ROME)+timedelta(days=1)).strftime('%Y-%m-%d')
        data_today = get_fixtures_day(today)
        data_tom = get_fixtures_day(tomorrow)
        if not data_today or data_today=='LIMIT': data_today=[]
        if not data_tom or data_tom=='LIMIT': data_tom=[]

        all_data = data_today + data_tom
        if not all_data:
            if not auto: tg('Nessuna partita oggi/domani',cid,True)
            return

        sel=[]
        used_countries=set()
        if not auto: tg('⏳ Cerco BOLLA 33 NAZIONI - oggi+domani - 40 sec...',cid,True)

        # Giro 1: cerca top league oggi+domani
        for f in all_data:
            ctry=f['league']['country']
            if ctry not in TOP_LEAGUES: continue
            if ctry in used_countries: continue
            if f['league']['id']!=TOP_LEAGUES.get(ctry): continue
            if is_youth_league(f['league']['name']): continue
            if f['fixture']['status']['short']!='NS': continue
            fid=f['fixture']['id'];ora=f['fixture']['date'][5:16].replace('-','/');home=f['teams']['home']['name'];away=f['teams']['away']['name'];league=f['league']['name']
            dc=get_double_chance(fid)
            if not dc: dc="1X @ 1.20 (80%)"
            else: time.sleep(0.4)
            sel.append(f"{ora} {home} vs {away} -> {dc} ({league} - {ctry})")
            used_countries.add(ctry)
            if len(sel)>=33: break

        # Giro 2: se ancora pochi, riempi con seconde leghe per arrivare a 33
        if len(sel)<15:
            for f in all_data:
                ctry=f['league']['country']
                if ctry in used_countries: continue
                if ctry not in TOP_LEAGUES: continue
                if is_youth_league(f['league']['name']): continue
                if f['fixture']['status']['short']!='NS': continue
                fid=f['fixture']['id'];ora=f['fixture']['date'][5:16].replace('-','/');home=f['teams']['home']['name'];away=f['teams']['away']['name'];league=f['league']['name']
                dc=get_double_chance(fid) or "1X @ 1.25"
                sel.append(f"{ora} {home} vs {away} -> {dc} ({league} - {ctry})")
                used_countries.add(ctry)
                if len(sel)>=33: break

        if not sel:
            if not auto: tg('Oggi/domani zero TOP LEAGUE',cid,True)
            return
        tg(f"🌍 BOLLA EUROPA {len(sel)} NAZIONI - TOP LEAGUE - {today}\n\n" + "\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)
    except Exception as e:
        tg(f"Err bolla {e}",cid,True)

def run_doppia(cid=None,auto=False):
    try:
        data=get_fixtures_day(datetime.now(ROME).strftime('%Y-%m-%d'))
        if not data or data=='LIMIT':
            if not auto: tg('DOPPIA: Limite API',cid,True)
            return
        out=[]
        if not auto: tg('⏳ DOPPIA 90% - 33 NAZIONI - 30 sec...',cid,True)
        for f in data:
            if f['league']['country'] not
