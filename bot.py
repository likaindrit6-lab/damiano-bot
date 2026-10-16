import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo

BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;av_g={};av_s=set();av_s_first=set()
# AGGIUNTA SOLO PER SFIGATA
av_sfiga_score={}

TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116,'Russia':235}

def is_youth_league(name):
    n=name.lower()
    bad=['u19','u21','u23','u17','women',' w ','female','youth','reserve','development','academy',' u18',' u20']
    return any(x in n for x in bad)

app=Flask(__name__)
@app.route('/')
def home():return f'BOT V37 ANGOLI PAID - {datetime.now(ITALY).strftime("%H:%M")}',200

TAST=json.dumps({"keyboard":[
["Serie A","Serie B","Inghilterra"],
["Spagna","Germania","Francia"],
["Olanda","Portogallo","Turchia"],
["DOPPIA ALTA %"],
["BOLLA EUROPA 33 NAZIONI"],
["📊 STATISTICHE 35 NAZIONI"],
["🚩 CALCIO D'ANGOLO +6"],
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

def get_corners_fixture(fid):
 try:
  u="https://v3.football.api-sports.io"+f"/fixtures/statistics?fixture={fid}"
  stats=api(u)
  if not stats or stats=='LIMIT' or len(stats)<2:return None
  tot=0;found=False
  for team in stats:
   for s in team['statistics']:
    if 'corner' in s['type'].lower():
     try:
      tot+=int(str(s['value'] or 0));found=True
     except:pass
  return tot if found else None
 except:return None

# ===== SOLO AGGIUNTA SFIGATA 4.5 =====
def get_sfigata(fid):
 try:
  u="https://v3.football.api-sports.io"+f"/odds?fixture={fid}"
  data=api(u)
  if not data or data=='LIMIT':return None
  for book in data[0].get('bookmakers',[])[:2]:
   for bet in book.get('bets',[]):
    if bet['name']=='Match Winner':
     q={}
     for v in bet['values']:
      try:q[v['value']]=float(v['odd'])
      except:pass
     h=q.get('Home',0);a=q.get('Away',0)
     if h>=4.5 and h>a and a<=1.8:return ('HOME',h,'AWAY',a)
     if a>=4.5 and a>h and h<=1.8:return ('AWAY',a,'HOME',h)
  return None
 except:return None

def media(league_id,name):
 txt=f"{name.upper()} - {datetime.now(ITALY).strftime('%d/%m %H:%M')}\n\n"
 u="https://v3.football.api-sports.io"+f"/teams?league={league_id}&season=2024"
 teams=api(u)
 if not teams or teams=='LIMIT':return f'Errore API {name}'
 for t in teams[:14]:
  tid=t['team']['id'];tname=t['team']['name']
  uu="https://v3.football.api-sports.io"+f"/fixtures?team={tid}&last=10&season=2024"
  last=api(uu)
  if not last or last=='LIMIT':time.sleep(0.4);continue
  tot=0;c=0
  for p in last:
   gh=p['goals']['home'];ga=p['goals']['away']
   if gh is None:continue
   tot+=gh+ga;c+=1
  if c==0:continue
  med=tot/c
  txt+=("PIU DI 2" if med>2 else "MENO DI 2")+f" - {tname}: {med:.2f}\n"
  time.sleep(0.3)
 return txt

def media_tutte_35(cid):
    tg("⏳ PARTITO STATISTICHE 35 NAZIONI - 4 min",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            res=media(lid, country)
            tg(res,cid,True)
            time.sleep(1)
        except:pass
    tg("✅ FINITO STATISTICHE 35 GOL",cid,True)

def media_angoli(league_id,name):
 txt=f"🚩 {name.upper()} - CORNER MEDIA ULTIME 10\n{datetime.now(ITALY).strftime('%d/%m')}\n\n"
 u="https://v3.football.api-sports.io"+f"/teams?league={league_id}&season=2025"
 teams=api(u)
 if not teams or teams=='LIMIT':
  uu="https://v3.football.api-sports.io"+f"/teams?league={league_id}&season=2024"
  teams=api(uu)
 if not teams or teams=='LIMIT':return f'Errore API {name}'
 trovati=0
 for t in teams[:14]:
  tid=t['team']['id'];tname=t['team']['name']
  uu="https://v3.football.api-sports.io"+f"/fixtures?team={tid}&last=10"
  last=api(uu)
  if not last or last=='LIMIT':time.sleep(0.4);continue
  tot_corners=0;c=0
  for p in last:
   if p['fixture']['status']['short']!='FT':continue
   fid=p['fixture']['id']
   corn=get_corners_fixture(fid)
   if corn is None:continue
   tot_corners+=corn;c+=1
   time.sleep(0.35)
  if c==0:continue
  med=tot_corners/c
  if med>=6.0:
   txt+=f"🔥 {tname}: {med:.1f} corner ({c} partite)\n"
   trovati+=1
  time.sleep(0.3)
 if trovati==0:
  txt+=f"Nessuna squadra con +6 corner in {name}\nMedia più bassa di 6"
 return txt

def media_tutte_angoli(cid):
    tg("⏳ PARTITO CALCIO D'ANGOLO +6 - 35 NAZIONI\nCi metto 8-10 minuti\nFiltro solo >6 corner/partita",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            res=media_angoli(lid, country)
            tg(res,cid,True)
            time.sleep(1)
        except Exception as e:
            tg(f"Errore {country}: {e}",cid,True)
    tg("✅ FINITO ANGOLI +6",cid,True)

def get_double_chance(fid):
 try:
  u="https://v3.football.api-sports.io"+f"/odds?fixture={fid}"
  data=api(u)
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
  u="https://v3.football.api-sports.io"+f"/odds?fixture={fid}"
  data=api(u)
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

def get_fixtures_today():
 today=datetime.now(ROME).strftime('%Y-%m-%d')
 u="https://v3.football.api-sports.io"+f"/fixtures?date={today}"
 return api(u)

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=='LIMIT':
  if not auto:tg('BOLLA: Limite API',cid,True)
  return
 sel=[]
 if not auto:tg('⏳ Cerco TOP LEAGUE + DOPPIA...',cid,True)
 for country,top_id in TOP_LEAGUES.items():
  found=None
  for f in data:
   if f['league']['id']==top_id and f['league']['country']==country:
    if is_youth_league(f['league']['name']):continue
    if f['fixture']['status']['short']!='NS':continue
    found=f;break
  if not found:continue
  fid=found['fixture']['id'];ora=found['fixture']['date'][11:16];home=found['teams']['home']['name'];away=found['teams']['away']['name'];league=found['league']['name']
  dc=get_double_chance(fid) or "1X"
  sel.append(f"{ora} {home} vs {away} -> {dc} ({league} - {country})")
  if len(sel)>=35:break
 if not sel:
  if not auto:tg('Oggi nessuna TOP LEAGUE in programma',cid,True)
  return
 tg(f"🌍 BOLLA EUROPA {len(sel)} NAZIONI\n\n" + '\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=='LIMIT':return
    out=[]
    if not auto:tg('⏳ Cerco OVER 1.5...',cid,True)
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
            time.sleep(0.4)
            if len(out)>=15:break
        except:continue
    if out:tg(f"🔥 DOPPIA {len(out)} OVER 1.5\n\n" + '\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,True)
    elif not auto:tg('🔥 Oggi nessun OVER 1.5 <1.55',cid,True)

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
     elif 'apri menu' in low:tg('✅ Menu aperto V37',cid,True,False);continue
     elif 'spegni' in low:is_paused=True;tg('⏸️ PAUSA',cid,True);continue
     elif 'accendi' in low or '/start' in low:is_paused=False;tg('▶️ V37 ATTIVO - ANGOLI FIX',cid,True);continue
     elif 'angolo' in low or 'calcio d' in low:
         threading.Thread(target=media_tutte_angoli,args=(cid,),daemon=True).start();continue
     elif 'statistiche 35' in low:
         threading.Thread(target=media_tutte_35,args=(cid,),daemon=True).start();continue
     elif 'status' in low:tg(f'STATUS V37 - {datetime.now(ITALY).strftime("%H:%M")}',cid,True);continue
     elif 'doppia' in low:run_doppia(cid);continue
     elif 'bolla' in low:run_bolla(cid);continue
  except:pass
  time.sleep(2)

def live_loop():
 tg('✅ BOT V37 ATTIVO\n🚩 CALCIO D\'ANGOLO +6 FIX PAID\n📊 STATS 35 GOL\n🌍 LIVE MONDO + SFIGATA 4.5',None,True)
 while True:
  try:
   if is_paused:time.sleep(30);continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:time.sleep(300);continue
   games=api('https://v3.football.api-sports.io'+'/fixtures?live=all')
   if games=='LIMIT':time.sleep(3600);continue
   if not games:time.sleep(60);continue
   for g in games:
    fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
    if m is None:continue
    home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
    # ===== SFIGATA GOAL CHECK - UNICA AGGIUNTA =====
    if fid not in av_sfiga_score:
     av_sfiga_score[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga_score[fid]
     if gh!=oh or ga!=oa:
      chi='HOME' if gh>oh else 'AWAY'
      av_sfiga_score[fid]=(gh,ga)
      sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       if chi==tipo:
        ns=home if tipo=='HOME' else away
        nf=away if tipo=='HOME' else home
        co=g['league']['country']
        txt=f"⚽ GOAL SFIGATA {m}' {co} {home} {gh}-{ga} {away}\n"
        txt+=f"Sfigata {ns} @{qs} segna!\n"
        txt+=f"Favorita {nf} @{qf} sotto\n"
        txt+=f"👉 RIGIOCA SUBITO GOL FAV / OVER"
        tg(txt)
    if 30<=m<=45 and fid not in av_s_first:
     u="https://v3.football.api-sports.io"+f"/fixtures/statistics?fixture={fid}"
     st=api(u);sot=0;corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if 'Shots on Goal' in x['type']:
         try:sot+=int(str(x['value'] or 0))
         except:pass
        if 'corner' in x['type'].lower():
         try:corn+=int(str(x['value'] or 0))
         except:pass
     if sot>=2 or corn>=4:tg(f"🔥 PRIMO TEMPO {m}' {g['league']['country']} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{corn}");av_s_first.add(fid)
    if 65<=m<=90 and fid not in av_s:
     u="https://v3.football.api-sports.io"+f"/fixtures/statistics?fixture={fid}"
     st=api(u);sot=0;corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if 'Shots on Goal' in x['type']:
         try:sot+=int(str(x['value'] or 0))
         except:pass
        if 'corner' in x['type'].lower():
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
