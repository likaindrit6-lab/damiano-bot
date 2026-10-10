import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;av_g={};av_s=set();av_s_first=set();last_bolla_hour=-1;last_doppia_hour=-1
# LOGICA NUOVA V32
preparati_sent=set();giocalo_sent=set();gol_tracker={};gol_fatto=set()

LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}
TOP_LEAGUES={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}
EUROPA_33=list(TOP_LEAGUES.keys())
ELITE_IDS=[135,39,140,78,61,88,94,144,203,179] # solo elite per MULTI ESATTI

def is_youth_league(name):
    if not name: return False
    n=name.lower()
    bad=['u19','u21','u23','u17','u18','u20','women',' w','w ','w-','female','femminile','ladies','girls','youth','reserve','development','academy','world']
    # blocca anche nomi squadra che finiscono con W
    if n.strip().endswith(' w'): return True
    return any(x in n for x in bad)

app=Flask(__name__)
@app.route('/')
def home():return f'BOT V32 MULTI ESATTI - {datetime.now(ITALY).strftime("%H:%M")}',200

TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["MULTI ESATTI"],["MODELLO AMERICANO 33"],["STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True})

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
  scores=sorted(scores, key=lambda x: x[1])[:5]
  return scores
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
    if is_youth_league(f['teams']['home']['name']):continue
    if is_youth_league(f['teams']['away']['name']):continue
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
            out.append(f"{ora} {home} vs {away} -> OVER 1.5 @ {over_odd} ({league})")
            time.sleep(0.6)
            if len(out)>=15:break
        except:continue
    if not out:
        if not auto:tg('🔥 Oggi nessun OVER 1.5 <1.55 nelle TOP LEAGUE pre-match',cid,True)
        return
    pref=f"🔥 DOPPIA ALTA % - {len(out)} OVER 1.5 PIU SICURI PRE-MATCH\n\n" if not auto else f"🔥 DOPPIA AUTOMATICA - {len(out)} OVER 1.5 SICURI PRE-MATCH\n\n"
    tg(pref+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,True)

def run_esatti(cid=None):
    data=get_fixtures_today()
    if not data or data=='LIMIT':
        tg('ESATTI: Limite API',cid,True);return
    tg('⏳ Cerco MULTI ESATTI 4-5 risultati x 8 BIG MATCH... 40 sec',cid,True)
    sel=[]
    for f in data:
        try:
            if f['league']['id'] not in ELITE_IDS:continue
            if is_youth_league(f['league']['name']):continue
            if f['fixture']['status']['short']!='NS':continue
            fid=f['fixture']['id']
            scores=get_correct_scores(fid)
            if not scores:continue
            ora=f['fixture']['date'][11:16];home=f['teams']['home']['name'];away=f['teams']['away']['name'];league=f['league']['name']
            txt_score=" | ".join([f"{s[0]} @{s[1]}" for s in scores])
            sel.append(f"{ora} {home} vs {away} ({league})\n -> {txt_score}")
            time.sleep(0.8)
            if len(sel)>=8:break
        except:continue
    if not sel:
        tg('Nessun big match con quote Correct Score oggi',cid,True);return
    tg(f"🎯 MULTI ESATTI - {len(sel)} BIG MATCH - 4/5 RISULTATI PIU PROBABILI\n\n" + "\n\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def run_americano(cid=None):run_bolla(cid,False)

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
     if 'spegni' in low:is_paused=True;tg('⏸️ PAUSA',cid,True)
     elif 'accendi' in low or '/start' in low:is_paused=False;tg('▶️ V32 ATTIVO - MULTI ESATTI',cid,True)
     elif 'status' in low:tg('STATUS: V32 LIVE 60/70 + ANTI-W + MULTI ESATTI',cid,True)
     elif 'doppia' in low:run_doppia(cid)
     elif 'esatti' in low:run_esatti(cid)
     elif 'bolla' in low or 'americano' in low:run_bolla(cid)
     elif low in [k.lower() for k in LEAGUES.keys()]:
      for k,v in LEAGUES.items():
       if k.lower()==low:tg(media(v,k),cid,True)
  except:pass
  time.sleep(2)

def live_loop():
 global last_bolla_hour,last_doppia_hour,preparati_sent,giocalo_sent,gol_tracker,gol_fatto,av_s_first
 tg('✅ BOT V32 ATTIVO\n🌍 ANTI-W / ANTI-U19\n⏰ 60 PREPARATI 1x / 70 GIOCALO 1x / GOL 1x\n🎯 NUOVO: MULTI ESATTI',keys=True)
 while True:
  try:
   if is_paused:time.sleep(30);continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:time.sleep(300);continue
   if now.hour!=last_bolla_hour and now.minute<10:
       last_bolla_hour=now.hour
       run_bolla(auto=True)
       time.sleep(5)
       run_doppia(auto=True)
   games=api('https://v3.football.api-sports.io/fixtures?live=all')
   if games=='LIMIT':time.sleep(3600);continue
   if not games:time.sleep(60);continue
   for g in games:
    try:
     # FILTRO ANTI DONNE / GIOVANILI
     if is_youth_league(g['league']['name']):continue
     if is_youth_league(g['teams']['home']['name']):continue
     if is_youth_league(g['teams']['away']['name']):continue
     fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
     if m is None:continue
     home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'] or 0;ga=g['goals']['away'] or 0
     tot_gol=gh+ga
     st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if x['type']=='Shots on Goal':
         try:sot+=int(str(x['value'] or 0).replace('%','') or 0)
         except:pass
     # ANTI-BUG: se 3 gol con 2 tiri, skip
     if tot_gol > sot and sot>0:continue
     # 1. PRIMO TEMPO 3 TIRI - UNA VOLTA
     if 30<=m<=45 and fid not in av_s_first:
      if sot>=3:
       tg(f"🔥 PRIMO TEMPO {m}' {g['league']['country']} {home} {gh}-{ga} {away} Tiri:{sot}")
       av_s_first.add(fid)
     # 2. PREPARATI 60' >5 TIRI - UNA VOLTA
     if m==60 and sot>5 and fid not in preparati_sent:
      tg(f"⚠️ PREPARATI 60' {g['league']['name']}\n{home} {gh}-{ga} {away}\n🎯 {sot} tiri - Tra 10 min GIOCALO")
      preparati_sent.add(fid)
     # 3. GIOCALO 70' - UNA VOLTA
     if m==70 and fid not in giocalo_sent:
      tg(f"🚀 GIOCALO ORA 70' {g['league']['name']}\n{home} {gh}-{ga} {away}\n🎯 {sot} tiri in porta")
      giocalo_sent.add(fid);gol_tracker[fid]=tot_gol
     # 4. DOPO 70' SOLO PRIMO GOL - POI MUTO
     if m>70 and fid in giocalo_sent and fid not in gol_fatto:
      if tot_gol>gol_tracker.get(fid,0):
       tg(f"✅ GOAL VINTO! {m}' {home} {gh}-{ga} {away} ({g['league']['name']})")
       gol_fatto.add(fid)
    except:continue
   time.sleep(60)
  except Exception as e:print(e);time.sleep(15)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
