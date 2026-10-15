import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;av_g={};av_s=set();av_s_first=set();last_bolla_hour=-1;last_doppia_hour=-1

TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116,'Russia':235}

def is_youth_league(name):
    n=name.lower()
    bad=['u19','u21','u23','u17','women',' w ','female','youth','reserve','development','academy',' u18',' u20']
    return any(x in n for x in bad)

app=Flask(__name__)
@app.route('/')
def home():return f'BOT V33 STATS 35 - {datetime.now(ITALY).strftime("%H:%M")}',200

TAST=json.dumps({"keyboard":[
["Serie A","Serie B","Inghilterra"],
["Spagna","Germania","Francia"],
["Olanda","Portogallo","Turchia"],
["DOPPIA ALTA %"],
["BOLLA EUROPA 33 NAZIONI"],
["📊 STATISTICHE 35 NAZIONI"],
["MODELLO AMERICANO 33"],
["STATUS"],
["ACCENDI","SPEGNI"],
["❌ CHIUDI MENU"]
],"resize_keyboard":True,"is_persistent":False})

TAST_CHIUSA=json.dumps({"keyboard":[["🎮 APRI MENU"]],"resize_keyboard":True,"is_persistent":False})

def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT:return
  base=f'https://api.telegram.org/bot{BOT}';pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys: pay['reply_markup']=json.loads(TAST_CHIUSA if chiusa else TAST)
  requests.post(base+'/sendMessage',json=pay,timeout=25)
 except:pass

def api(url):
 try:
  r=requests.get(url,headers={'x-apisports-key':KEY},timeout=30)
  if r.status_code==429:return 'LIMIT'
  return r.json().get('response',[])
 except:return []

def media(league_id,name,cid=None):
 txt=f"{name.upper()} - {datetime.now(ITALY).strftime('%d/%m %H:%M')}\n\n"
 teams=api(f'https://v3.football.api-sports.io/teams?league={league_id}&season=2024')
 if not teams or teams=='LIMIT':return 'Errore API o limite'
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
  txt+=("PIU DI 2" if med>2 else "MENO DI 2")+f" - {tname}: {med:.2f}\n"
  time.sleep(0.35)
 return txt

def media_tutte_35(cid):
    tg(f"⏳ PARTITO STATISTICHE 35 NAZIONI\nCi metto 4-5 minuti, ti mando 1 messaggio per nazione\nInizio da Italia...",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            if is_youth_league(country):continue
            res = media(lid, f"{country} - ID {lid}", cid)
            tg(res, cid, True)
            time.sleep(2)
        except Exception as e:
            tg(f"Errore {country}: {e}", cid, True)
    tg("✅ FINITO STATISTICHE 35 NAZIONI",cid,True)

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

def get_fixtures_today():
 today=datetime.now(ROME).strftime('%Y-%m-%d')
 return api(f'https://v3.football.api-sports.io/fixtures?date={today}')

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
    found=f;break
  if not found:continue
  fid=found['fixture']['id'];ora=found['fixture']['date'][11:16];home=found['teams']['home']['name'];away=found['teams']['away']['name'];league=found['league']['name']
  dc=get_double_chance(fid)
  if not dc:dc="1X (no quota)"
  else:time.sleep(0.6)
  sel.append(f"{ora} {home} vs {away} -> {dc} ({league} - {country})")
  if len(sel)>=35:break
 if not sel:
  if not auto:tg('Oggi nessuna TOP LEAGUE in programma (pre-match)',cid,True)
  return
 tg(f"🌍 BOLLA EUROPA {len(sel)} NAZIONI\n\n" + '\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=='LIMIT':
        if not auto:tg('DOPPIA: Limite API',cid,True)
        return
    out=[]
    if not auto:tg('⏳ Cerco OVER 1.5 PIU SICURI...',cid,True)
    for f in data:
        try:
            if f['league']['country'] not in TOP_LEAGUES:continue
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
        if not auto:tg('🔥 Oggi nessun OVER 1.5 <1.55',cid,True)
        return
    tg(f"🔥 DOPPIA {len(out)} OVER 1.5 SICURI\n\n" + '\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,True)

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
     if 'chiudi menu' in low:tg('✅ Menu chiuso',cid,True,True);continue
     elif 'apri menu' in low:tg('✅ Menu aperto',cid,True,False);continue
     elif 'spegni' in low:is_paused=True;tg('⏸️ PAUSA',cid,True);continue
     elif 'accendi' in low or '/start' in low:is_paused=False;tg('▶️ V33 ATTIVO - 35 NAZIONI',cid,True);continue
     elif 'statistiche 35' in low or 'stat 35' in low:
         threading.Thread(target=media_tutte_35,args=(cid,),daemon=True).start()
         continue
     elif 'status' in low:tg(f'STATUS V33 - {datetime.now(ITALY).strftime("%H:%M")}',cid,True);continue
     elif 'doppia' in low:run_doppia(cid);continue
     elif 'bolla' in low or 'americano' in low:run_bolla(cid);continue
  except:pass
  time.sleep(2)

def live_loop():
 tg('✅ BOT V33 ATTIVO\n📊 NUOVO TASTO: STATISTICHE 35 NAZIONI\n🌍 LIVE MONDO\n🇪🇺 BOLLA 35',None,True)
 while True:
  try:
   if is_paused:time.sleep(30);continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:time.sleep(300);continue
   games=api('https://v3.football.api-sports.io/fixtures?live=all')
   if games=='LIMIT':time.sleep(3600);continue
   if not games:time.sleep(60);continue
   for g in games:
    fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
    if m is None:continue
    home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
    if 30<=m<=45 and fid not in av_s_first:
     st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0;corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if 'Shots on Goal' in x['type']:
         try:sot+=int(str(x['value'] or 0))
         except:pass
        if 'Corner' in x['type']:
         try:corn+=int(str(x['value'] or 0))
         except:pass
     if sot>=2:tg(f"🔥 PRIMO TEMPO {m}' {g['league']['country']} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{corn}");av_s_first.add(fid)
    if 65<=m<=90 and fid not in av_s:
     st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0;corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if 'Shots on Goal' in x['type']:
         try:sot+=int(str(x['value'] or 0))
         except:pass
        if 'Corner' in x['type']:
         try:corn+=int(str(x['value'] or 0))
         except:pass
     if sot>=4 or corn>=6:tg(f"🚀 GIOCALO {m}' {g['league']['country']} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{corn}");av_s.add(fid);av_g[fid]=gh+ga
   for g in games:
    fid=g['fixture']['id']
    if fid in av_g:
     tot=g['goals']['home']+g['goals']['away']
     if tot>av_g[fid]:tg(f"✅ GOAL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
   time.sleep(60)
  except Exception as e:print(e);time.sleep(15)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
