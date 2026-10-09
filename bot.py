import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));ROME=ZoneInfo("Europe/Rome")
is_paused=False;last_id=0;av_g={};av_s=set();av_s_first=set();last_bolla_hour=-1
LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}
app=Flask(__name__)
@app.route('/')
def home():return f'BOT V23 COMPLETO - {datetime.now(ITALY).strftime("%H:%M")}',200
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["MODELLO AMERICANO 33"],["STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True})
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
def media(league_id,name):
 txt=f'{name.upper()} - MEDIA ULTIME 10\n{datetime.now(ITALY).strftime("%d/%m %H:%M")}\n\n'
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
  txt+=f"{'PIU' DI 2' if med>2 else 'MENO DI 2'} - {tname}: {med:.2f}\n"
  time.sleep(0.4)
 return txt
def get_fixtures_today():
 today=datetime.now(ROME).strftime('%Y-%m-%d')
 return api(f'https://v3.football.api-sports.io/fixtures?date={today}')
def run_doppia(cid=None):
 data=get_fixtures_today();out=[]
 for f in data:
  try:
   if f['fixture']['id'] in av_g:continue
   h=f['goals']['home'];a=f['goals']['away']
   if h is None or a is None:continue
   if h+a>=2:out.append(f"{f['teams']['home']['name']}-{f['teams']['away']['name']} {h}-{a}")
  except:continue
 tg('DOPPIA: Nessun match' if not out else '🔥 DOPPIA ALTA %\n'+'\n'.join(out[:20]),cid,True)
def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=='LIMIT':
  if not auto:tg('BOLLA: Limite API',cid,True)
  return
 sel=[];seen=set()
 for f in data:
  try:
   c=f['league']['country']
   if c in seen:continue
   sel.append(f"{f['fixture']['date'][11:16]} {f['teams']['home']['name']} vs {f['teams']['away']['name']} -> 12 100%")
   seen.add(c)
   if len(sel)>=33:break
  except:continue
 if sel:
  pref="🌍 BOLLA ORARIA\n" if auto else "🌍 BOLLA 33\n"
  tg(pref+'\n'.join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)
def run_americano(cid=None):
 data=get_fixtures_today();picks=[f"{f['teams']['home']['name']} - {f['teams']['away']['name']}" for f in data[:33]]
 tg('🇺🇸 AMERICANO 33\n'+'\n'.join([f"{i}. {m} | ML | O/U" for i,m in enumerate(picks)]),cid,True)
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
     elif 'accendi' in low or '/start' in low:is_paused=False;tg('ATTIVO V23',cid,True)
     elif 'status' in low:tg(f'STATUS: {"PAUSA" if is_paused else "ATTIVO"}',cid,True)
     elif 'doppia' in low:run_doppia(cid)
     elif 'bolla' in low:run_bolla(cid)
     elif 'americano' in low:run_americano(cid)
     elif low in [k.lower() for k in LEAGUES.keys()]:
      for k,v in LEAGUES.items():
       if k.lower()==low:tg(media(v,k),cid,True)
  except:pass
  time.sleep(2)
def live_loop():
 global last_bolla_hour
 tg('BOT V23 COMPLETO ATTIVO - LIVE + MEDIA + BOLLA ORARIA',keys=True)
 while True:
  try:
   if is_paused:time.sleep(30);continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:time.sleep(300);continue
   if now.hour!=last_bolla_hour and now.minute<5:last_bolla_hour=now.hour;run_bolla(auto=True)
   games=api('https://v3.football.api-sports.io/fixtures?live=all')
   if games=='LIMIT':time.sleep(3600);continue
   if not games:time.sleep(60);continue
   games=[g for g in games if g['league']['id'] in LEAGUES.values()]
   for g in games:
    fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
    if m is None:continue
    home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
    if 30<=m<=45 and fid not in av_s_first:
     st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if x['type']=='Shots on Goal':
         try:sot+=int(str(x['value'] or 0).replace('%','') or 0)
         except:pass
     if sot>=2:tg(f"PRIMO TEMPO {m}' {g['league']['country']} {home} {gh}-{ga} {away} Tiri:{sot}");av_s_first.add(fid)
    if 65<=m<=90 and fid not in av_s:
     st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}');sot=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if x['type']=='Shots on Goal':
         try:sot+=int(str(x['value'] or 0).replace('%','') or 0)
         except:pass
     if sot>=4:tg(f"GIOCALO {m}' {g['league']['country']} {home} {gh}-{ga} {away} Tiri:{sot}");av_s.add(fid);av_g[fid]=gh+ga
   for g in games:
    fid=g['fixture']['id']
    if fid in av_g:
     tot=g['goals']['home']+g['goals']['away']
     if tot>av_g[fid]:tg(f"GOAL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
   time.sleep(60)
  except Exception as e:print(e);time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
