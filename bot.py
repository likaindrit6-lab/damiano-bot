import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;last_bolla_hour=-1
sot_sent=set();corner_sent=set();gol_tracker={};gol_fatto=set()
corner_pre_cache={};av_s_first=set()

LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}
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
def home():return f'BOT V33.3 GRANDE - {datetime.now(ITALY).strftime("%H:%M")}',200

# TASTIERA GROSSA - TUTTO DENTRO - NIENTE FUORI
TAST=json.dumps({"keyboard":[
    ["SERIE A","SERIE B"],
    ["INGHILTERRA","SPAGNA","GERMANIA"],
    ["FRANCIA","OLANDA","PORTOGALLO"],
    ["TURCHIA","BELGIO"],
    ["CORNER 90%","MULTIGOL"],
    ["DOPPIA ALTA %","SOT 5 LIVE"],
    ["BOLLA EUROPA 33"],
    ["MULTI ESATTI","MODELLO AMERICANO"],
    ["STATUS","SPEGNI","ACCENDI"]
],"resize_keyboard":True})

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
    if 'Over/Under' in bet['name']:
     for v in bet['values']:
      if 'Over 1.5' in v['value']:
       try:return float(v['odd'])
       except:continue
 except:pass
 return None

def get_corner_over_75(fid):
 try:
  data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
  if not data or data=='LIMIT':return False
  for book in data[0].get('bookmakers',[])[:3]:
   for bet in book.get('bets',[]):
    if 'corner' in bet['name'].lower():
     for v in bet['values']:
      if 'Over 7.5' in v['value'] or 'Over 7,5' in v['value']:
       try:
        if float(v['odd']) < 1.90: return True
       except:continue
  return False
 except:return False

def get_correct_scores(fid):
 try:
  data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
  if not data or data=='LIMIT':return []
  scores=[]
  for book in data[0].get('bookmakers',[])[:2]:
   for bet in book.get('bets',[]):
    if 'Correct Score' in bet['name']:
     for v in bet['values']:
      try:scores.append((v['value'], float(v['odd'])))
      except:continue
  scores=sorted(scores, key=lambda x: x[1])
  seen=set();uniq=[]
  for s,o in scores:
   if s not in seen:
    seen.add(s);uniq.append(s)
   if len(uniq)>=5:break
  return uniq
 except:return []

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
 return api(f'https://v3.football.api-sports.io/fixtures?date={today}')

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data
