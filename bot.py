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
def home():return f'BOT V33 CLEAN - {datetime.now(ITALY).strftime("%H:%M")}',200

TAST=json.dumps({"keyboard":[["SERIE A","SERIE B"],["INGHILTERRA","SPAGNA","GERMANIA"],["FRANCIA","OLANDA","PORTOGALLO"],["DOPPIA ALTA %"],["BOLLA EUROPA 33"],["MULTI ESATTI","MODELLO AMERICANO"],["STATUS","SPEGNI","ACCENDI"]],"resize_keyboard":True})

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

def get_corner_over_75(fid):
 try:
  data=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
  if not data or data=='LIMIT':return False
  for book in data[0].get('bookmakers',[])[:3]:
   for bet in book.get('bets',[]):
    bn=bet['name'].lower()
    if 'corner' in bn:
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
      try:
       odd=float(v['odd'])
       scores.append((v['value'], odd))
      except:continue
  scores=sorted(scores, key=lambda x: x[1])
  seen=set();uniq=[]
  for s,o in scores:
   if s not in seen:
    seen.add(s);uniq.append(s)
   if len(uniq)>=5:break
  return uniq
 except:return []

def get_fixtures_today():
 today=datetime.now(ROME).strftime('%Y-%m-%d')
 return api(f'https://v3.football.api-sports.io/fixtures?date={today}')

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=='LIMIT':
  if not auto:tg('BOLLA: Limite API',cid,True);return
 sel=[]
 if not auto:tg('Cerco TOP LEAGUE... 30 sec',cid,True)
 for country,top_id in TOP_LEAGUES.items():
  found=None
  for f in data:
   if f['league']['id']==top_id and f['league']['country']==country:
    if is_youth_league(f['league']['name']):continue
    if is_youth_league(f['teams']['home']['name']):continue
    if is_youth_league(f['teams']['away']['name']):continue
    if f['fixture']['status']['short']!='NS':continue
    found=f;break
  if not found:continue
  fid=found['fixture']['id'];ora=found['fixture']['date'][11:16];home=found['teams']['home']['name'];away=found['teams']['away']['name'];league=found['league']['name']
  dc=get_double_chance(fid)
  if not dc:dc="1X (no quota)"
  else:time.sleep(0.6)
  sel.append(f"{ora} {home} vs {away} -> {dc} ({league})")
  if len(sel)>=33:break
 if not sel:
  if not auto:tg('Oggi nessuna TOP LEAGUE',cid,True);return
 tg(f"BOLLA EUROPA {len(sel)} NAZIONI\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def run_doppia(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=='LIMIT':
  if not auto:tg('DOPPIA: Limite API',cid,True);return
 out=[]
 if not auto:tg('Cerco OVER 1.5... 30 sec',cid,True)
 for f in data:
  try:
   if f['league']['country'] not in EUROPA_33:continue
   if is_youth_league(f['league']['name']):continue
   if f['fixture']['status']['short']!='NS':continue
   if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']):continue
   fid=f['fixture']['id']
   over_odd=get_over_15(fid)
   if over_odd is None or over_odd>1.55:continue
   ora=f['fixture']['date'][11:16];home=f['teams']['home']['name'];away=f['teams']['away']['name'];league=f['league']['name']
   out.append(f"{ora} {home} vs {away} -> OVER 1.5 @ {over_odd} ({league})")
   time.sleep(0.6)
   if len(out)>=15:break
  except:continue
 if not out:
  if not auto:tg('Nessun OVER 1.5 <1.55 oggi',cid,True);return
 tg(f"DOPPIA ALTA % - {len(out)} OVER 1.5\n\n"+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,True)

def run_esatti(cid=None):
 data=get_fixtures_today()
 if not data or data=='LIMIT':tg('ESATTI: Limite API',cid,True);return
 tg('Cerco 5 RISULTATI x TOP EUROPA... 40 sec',cid,True)
 sel=[]
 for f in data:
  try:
   if f['league']['country'] not in EUROPA_33:continue
   if f['league']['id']!=TOP_LEAGUES.get(f['league']['country']):continue
   if is_youth_league(f['league']['name']):continue
   if is_youth_league(f['teams']['home']['name']):continue
   if is_youth_league(f['teams']['away']['name']):continue
   if f['fixture']['status']['short']!='NS':continue
   fid=f['fixture']['id']
   scores=get_correct_scores(fid)
   if len(scores)<3:continue
   ora=f['fixture']['date'][11:16];home=f['teams']['home']['name'];away=f['teams']['away']['name'];league=f['league']['name']
   txt_score=" - ".join(scores[:5])
   sel.append(f"{ora} {home} vs {away} ({league})\n -> {txt_score}")
   time.sleep(0.8)
   if len(sel)>=10:break
  except:continue
 if not sel:tg('Nessun big match oggi',cid,True);return
 tg(f"MULTI ESATTI - {len(sel)} PARTITE - 5 RISULTATI\n\n" + "\n\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def poll():
 global is_paused,last_id
 try:
  if BOT:requests.get(f'https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true',timeout=10)
 except:pass
 while True:
  try:
   if not BOT:time.sleep(60);continue
   base=f'https://api.telegram.org/bot{BOT}';url=base+f'/getUpdates?offset={last_id+1}&timeout=20'
   r=requests.get(url,timeout=30).json()
   if r.get('ok'):
    for u in r.get('result',[]):
     last_id=u['update_id'];msg=u.get('message',{});txt=(msg.get('text') or '').strip();low=txt.lower();cid=msg.get('chat',{}).get('id')
     if not txt:continue
     if 'spegni' in low:is_paused=True;tg('PAUSA',cid,True)
     elif 'accendi' in low or '/start' in low:is_paused=False;tg('V33 FINALE ATTIVO - SOT<70 + CORNER 90%',cid,True)
     elif 'status' in low:tg('STATUS V33 FINALE: SOT 5 sotto 70 + CORNER 90% + ESATTI 5 risultati',cid,True)
     elif 'doppia' in low:run_doppia(cid)
     elif 'esatti' in low:run_esatti(cid)
     elif 'bolla' in low or 'americano' in low:run_bolla(cid)
  except:pass
  time.sleep(2)

def live_loop():
 global last_bolla_hour,sot_sent,corner_sent,gol_tracker,gol_fatto,av_s_first
 tg('BOT V33 FINALE ATTIVO - SOT 5 SOTTO 70 + CORNER 90% + ESATTI 5 RISULTATI',keys=True)
 while True:
  try:
   if is_paused:time.sleep(30);continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:time.sleep(300);continue
   if now.hour!=last_bolla_hour and now.minute<10:
       last_bolla_hour=now.hour
       run_bolla(auto=True);time.sleep(5);run_doppia(auto=True)
   games=api('https://v3.football.api-sports.io/fixtures?live=all')
   if games=='LIMIT':time.sleep(3600);continue
   if not games:time.sleep(60);continue
   for g in games:
    try:
     if is_youth_league(g['league']['name']):continue
     if is_youth_league(g['teams']['home']['name']):continue
     if is_youth_league(g['teams']['away']['name']):continue
     fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
     if m is None:continue
     home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'] or 0;ga=g['goals']['away'] or 0
     tot_gol=gh+ga
     st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
     sot=0;corners=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if x['type']=='Shots on Goal':
         try:sot+=int(str(x['value'] or 0).replace('%','') or 0)
         except:pass
        if x['type']=='Corner Kicks':
         try:corners+=int(str(x['value'] or 0) or 0)
         except:pass
     if tot_gol > sot and sot>0:continue
     if 30<=m<=45 and fid not in av_s_first and sot>=3:
       tg(f"PRIMO TEMPO {m}' {home} {gh}-{ga} {away} Tiri:{sot}")
       av_s_first.add(fid)
     if m < 70 and fid not in sot_sent and sot >= 5:
       tg(f"GIOCALO {m}' {home} {gh}-{ga} {away} - {sot} TIRI SOTTO 70 - PERCENTUALE ALTA\n{g['league']['name']}")
       sot_sent.add(fid);gol_tracker[fid]=tot_gol
     if fid not in corner_pre_cache:
      corner_pre_cache[fid]=get_corner_over_75(fid)
      time.sleep(0.4)
     if corner_pre_cache.get(fid) and fid not in corner_sent and corners >= 7:
       tg(f"CORNER 90% USCITA! {m}' {home} vs {away} - {corners} CORNER - OVER 7.5 AL 90%\n{g['league']['name']}")
       corner_sent.add(fid)
     if fid in sot_sent and fid not in gol_fatto:
      if tot_gol > gol_tracker.get(fid,0):
       tg(f"GOAL VINTO! {m}' {home} {gh}-{ga} {away} - Era {sot} tiri")
       gol_fatto.add(fid)
    except:continue
   time.sleep(45)
  except Exception as e:print(e);time.sleep(15)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
