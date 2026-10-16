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
av_g={}
av_s=set()
av_s_first=set()
av_score={}

TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116,'Russia':235}

def is_youth_league(name):
    n=name.lower()
    bad=['u19','u21','u23','u17','women',' w ','female','youth','reserve','development','academy',' u18',' u20']
    for x in bad:
        if x in n:
            return True
    return False

app=Flask(__name__)
@app.route('/')
def home():
    return "BOT V38 ULTRA FIX 2 - " + datetime.now(ITALY).strftime("%H:%M"),200

TAST=json.dumps({"keyboard":[
["Serie A","Serie B","Inghilterra"],
["Spagna","Germania","Francia"],
["Olanda","Portogallo","Turchia"],
["DOPPIA ALTA %"],
["BOLLA EUROPA 33 NAZIONI"],
["STATISTICHE 35 NAZIONI"],
["CALCIO D'ANGOLO +6"],
["STATUS"],
["ACCENDI","SPEGNI"],
["CHIUDI MENU"]
],"resize_keyboard":True,"is_persistent":False})

TAST_CHIUSA=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True,"is_persistent":False})

def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT:
   return
  base="https://api.telegram.org/bot" + BOT
  pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys:
   pay['reply_markup']=json.loads(TAST_CHIUSA if chiusa else TAST)
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

def get_corners_fixture(fid):
 try:
  url="https://v3.football.api-sports.io/fixtures/statistics?fixture=" + str(fid)
  stats=api(url)
  if not stats or stats=='LIMIT' or len(stats)<2:
   return None
  tot=0
  found=False
  for team in stats:
   for s in team['statistics']:
    if 'corner' in s['type'].lower():
     try:
      tot+=int(str(s['value'] or 0))
      found=True
     except:
      pass
  if found:
   return tot
  return None
 except:
  return None

SOGLIA_SFIGATA=4.5
def get_sfigata(fid):
 try:
  url="https://v3.football.api-sports.io/odds?fixture=" + str(fid)
  data=api(url)
  if not data or data=='LIMIT':
   return None
  for book in data[0].get('bookmakers',[])[:2]:
   for bet in book.get('bets',[]):
    if bet['name']=='Match Winner':
     q={}
     for v in bet['values']:
      try:
       q[v['value']]=float(v['odd'])
      except:
       pass
     h=q.get('Home',0)
     a=q.get('Away',0)
     if h>=SOGLIA_SFIGATA and h>a and a<=1.80:
      return ('HOME',h,'AWAY',a)
     if a>=SOGLIA_SFIGATA and a>h and h<=1.80:
      return ('AWAY',a,'HOME',h)
  return None
 except:
  return None

def media(league_id,name):
 txt=name.upper() + " - " + datetime.now(ITALY).strftime('%d/%m %H:%M') + "\n\n"
 url1="https://v3.football.api-sports.io/teams?league=" + str(league_id) + "&season=2024"
 teams=api(url1)
 if not teams or teams=='LIMIT':
  return "Errore " + name
 for t in teams[:14]:
  tid=t['team']['id']
  tname=t['team']['name']
  url2="https://v3.football.api-sports.io/fixtures?team=" + str(tid) + "&last=10&season=2024"
  last=api(url2)
  if not last or last=='LIMIT':
   continue
  tot=0
  c=0
  for p in last:
   gh=p['goals']['home']
   ga=p['goals']['away']
   if gh is None:
    continue
   tot+=gh+ga
   c+=1
  if c==0:
   continue
  med=tot/c
  if med>2:
   txt+="PIU DI 2 - " + tname + ": " + "{:.2f}".format(med) + "\n"
  else:
   txt+="MENO DI 2 - " + tname + ": " + "{:.2f}".format(med) + "\n"
 return txt

def media_tutte_35(cid):
    tg("PARTITO STATS 35 NAZIONI",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            res=media(lid, country)
            tg(res,cid,True)
        except:
            pass
    tg("FINITO STATS 35",cid,True)

def media_angoli(league_id,name):
 txt=name.upper() + " - CORNER MEDIA\n" + datetime.now(ITALY).strftime('%d/%m') + "\n\n"
 url1="https://v3.football.api-sports.io/teams?league=" + str(league_id) + "&season=2025"
 teams=api(url1)
 if not teams or teams=='LIMIT':
  url2="https://v3.football.api-sports.io/teams?league=" + str(league_id) + "&season=2024"
  teams=api(url2)
 if not teams or teams=='LIMIT':
  return "Errore " + name
 trovati=0
 for t in teams[:14]:
  tid=t['team']['id']
  tname=t['team']['name']
  url3="https://v3.football.api-sports.io/fixtures?team=" + str(tid) + "&last=10"
  last=api(url3)
  if not last or last=='LIMIT':
   continue
  tot_corners=0
  c=0
  for p in last:
   if p['fixture']['status']['short']!='FT':
    continue
   corn=get_corners_fixture(p['fixture']['id'])
   if corn is None:
    continue
   tot_corners+=corn
   c+=1
  if c==0:
   continue
  med=tot_corners/c
  if med>=6.0:
   txt+=tname + ": " + "{:.1f}".format(med) + " corner (" + str(c) + ")\n"
   trovati+=1
 if trovati==0:
  txt+="Nessuna +6 in " + name + "\n"
 return txt

def media_tutte_angoli(cid):
    tg("PARTITO ANGOLI +6 - 35 NAZIONI",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            res=media_angoli(lid, country)
            tg(res,cid,True)
        except Exception as e:
            tg("Errore " + country + ": " + str(e),cid,True)
    tg("FINITO ANGOLI +6 ULTRA",cid,True)

def get_double_chance(fid):
 try:
  url="https://v3.football.api-sports.io/odds?fixture=" + str(fid)
  data=api(url)
  if not data or data=='LIMIT':
   return None
  for book in data[0].get('bookmakers',[])[:3]:
   for bet in book.get('bets',[]):
    if 'Double Chance' in bet['name']:
     best=None
     best_odd=10
     for v in bet['values']:
      try:
       odd=float(v['odd'])
       if odd<best_odd:
        best_odd=odd
        best=v['value']
      except:
       continue
     if best:
      if 'Home/Draw' in best:
       return "1X @ " + str(best_odd)
      if 'Draw/Away' in best:
       return "X2 @ " + str(best_odd)
      if 'Home/Away' in best:
       return "12 @ " + str(best_odd)
 except:
  pass
 return None

def get_over_15(fid):
 try:
  url="https://v3.football.api-sports.io/odds?fixture=" + str(fid)
  data=api(url)
  if not data or data=='LIMIT':
   return None
  for book in data[0].get('bookmakers',[])[:3]:
   for bet in book.get('bets',[]):
    if 'Over/Under' in bet['name']:
     for v in bet['values']:
      if 'Over 1.5' in v['value']:
       try:
        return float(v['odd'])
       except:
        continue
 except:
  pass
 return None

def get_fixtures_today():
 today=datetime.now(ROME).strftime('%Y-%m-%d')
 url="https://v3.football.api-sports.io/fixtures?date=" + today
 return api(url)

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=='LIMIT':
  return
 sel=[]
 if not auto:
  tg("Cerco BOLLA EUROPA...",cid,True)
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
  dc=get_double_chance(fid) or "1X"
  sel.append(ora + " " + home + " vs " + away + " -> " + dc + " (" + league + ")")
  if len(sel)>=35:
   break
 if sel:
  txt="BOLLA " + str(len(sel)) + " NAZIONI\n\n"
  for i,m in enumerate(sel):
   txt+=str(i+1) + ". " + m + "\n"
  tg(txt,cid,True)

def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=='LIMIT':
     return
    out=[]
    if not auto:
     tg("Cerco OVER 1.5...",cid,True)
    for f in data:
        try:
            if f['league']['country'] not in TOP_LEAGUES:
             continue
            if is_youth_league(f['league']['name']):
             continue
            if f['fixture']['status']['short']!='NS':
             continue
            if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']):
             continue
            fid=f['fixture']['id']
            over_odd=get_over_15(fid)
            if over_odd is None or over_odd>1.55:
             continue
            ora=f['fixture']['date'][11:16]
            home=f['teams']['home']['name']
            away=f['teams']['away']['name']
            league=f['league']['name']
            out.append(ora + " " + home + " vs " + away + " -> OVER 1.5 @ " + str(over_odd) + " (" + league + ")")
            if len(out)>=15:
             break
        except:
         continue
    if out:
     txt="DOPPIA " + str(len(out)) + " OVER 1.5\n\n"
     for i,m in enumerate(out):
      txt+=str(i+1) + ". " + m + "\n"
     tg(txt,cid,True)

def poll():
 global is_paused,last_id
 try:
  if BOT:
   requests.get("https://api.telegram.org/bot" + BOT + "/deleteWebhook?drop_pending_updates=true",timeout=10)
 except:
  pass
 while True:
  try:
   if not BOT:
    time.sleep(60)
    continue
   base="https://api.telegram.org/bot" + BOT
   url=base + "/getUpdates?offset=" + str(last_id+1) + "&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get('ok'):
    for u in r.get('result',[]):
     last_id=u['update_id']
     msg=u.get('message',{})
     txt=(msg.get('text') or '').strip()
     low=txt.lower()
     cid=msg.get('chat',{}).get('id')
     if not txt:
      continue
     if 'chiudi menu' in low:
      tg('Menu chiuso',cid,True,True)
      continue
     elif 'apri menu' in low:
      tg('Menu aperto V38 ULTRA FIX 2',cid,True,False)
      continue
     elif 'spegni' in low:
      is_paused=True
      tg('PAUSA',cid,True)
      continue
     elif 'accendi' in low or '/start' in low:
      is_paused=False
      tg('V38 ULTRA FIX 2 ATTIVO',cid,True)
      continue
     elif 'angolo' in low:
         threading.Thread(target=media_tutte_angoli,args=(cid,),daemon=True).start()
         continue
     elif 'statistiche 35' in low:
         threading.Thread(target=media_tutte_35,args=(cid,),daemon=True).start()
         continue
     elif 'status' in low:
      tg("STATUS V38 ULTRA - " + datetime.now(ITALY).strftime("%H:%M"),cid,True)
      continue
     elif 'doppia' in low:
      run_doppia(cid)
      continue
     elif 'bolla' in low:
      run_bolla(cid)
      continue
  except:
   pass
  time.sleep(1)

def live_loop():
 tg('BOT V38 ULTRA FIX 2 ATTIVO - GOAL SFIGATA 4.50+ - ANGOLI +6 - 450/min',None,True)
 while True:
  try:
   if is_paused:
    time.sleep(10)
    continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:
    time.sleep(120)
    continue
   games=api('https://v3.football.api-sports.io/fixtures?live=all')
   if games=='LIMIT':
    time.sleep(20)
    continue
   if not games:
    time.sleep(15)
    continue
   for g in games:
    fid=g['fixture']['id']
    m=g['fixture']['status']['elapsed']
    if m is None:
     continue
    home=g['teams']['home']['name']
    away=g['teams']['away']['name']
    gh=g['goals']['home']
    ga=g['goals']['away']
    if fid not in av_score:
     av_score[fid]=(gh,ga)
    else:
     old_h,old_a=av_score[fid]
     if gh!=old_h or ga!=old_a:
      chi='HOME' if gh>old_h else 'AWAY'
      av_score[fid]=(gh,ga)
      sfiga=get_sfigata(fid)
      if sfiga:
       tipo_sfiga,quota_sfiga,tipo_favo,quota_favo=sfiga
       if chi==tipo_sfiga:
        nome_sfiga=home if tipo_sfiga=='HOME' else away
        nome_favo=away if tipo_sfiga=='HOME' else home
        country=g['league']['country']
        msg="GOAL SFIGATA " + str(m) + "' " + country + " " + home + " " + str(gh) + "-" + str(ga) + " " + away + "\n"
        msg+="Sfigata " + nome_sfiga + " @" + str(quota_sfiga) + " segna!\n"
        msg+="Favorita " + nome_favo + " @" + str(quota_favo) + " sotto\n"
        msg+="RIGIOCA SUBITO GOL FAVORITA / OVER"
        tg(msg)
    if 30<=m<=45 and fid not in av_s_first:
     url="https://v3.football.api-s
