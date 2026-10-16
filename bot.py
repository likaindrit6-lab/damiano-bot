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
    return "BOT V38 ULTRA - " + datetime.now(ITALY).strftime("%H:%M"),200

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
  base_tg="https://api.telegram.org/bot" + BOT
  pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys:
   pay['reply_markup']=json.loads(TAST_CHIUSA if chiusa else TAST)
  requests.post(base_tg+'/sendMessage',json=pay,timeout=25)
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
            tg(media(lid,country),cid,True)
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

def media_tutte_angoli(cid
