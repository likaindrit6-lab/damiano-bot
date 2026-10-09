import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_id=0;av_g={};av_s=set();pre=set();pre1=set();cache={}
LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Olanda':88,'Portogallo':94,'Belgio':144,'Francia':61}
app=Flask(__name__)
@app.route('/')
def home():return f'BOT OK - {datetime.now(ITALY).strftime("%H:%M")}',200
TAST=json.dumps({'keyboard':[['Serie A','Serie B'],['Inghilterra','Spagna'],['Olanda','Portogallo'],['Francia','Belgio'],['ACCENDI','SPEGNI']],'resize_keyboard':True})

def tg(m,cid=None,keys=False):
 try:
  cid=cid or CHAT;base=f'https://api.telegram.org/bot{BOT}';pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys:pay['reply_markup']=TAST
  requests.post(base+'/sendMessage',json=pay,timeout=20)
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
  # QUI E' LA MODIFICA CHE MI HAI CHIESTO TU
  if med>2:
   etichetta="PIU' DI 2"
  else:
   etichetta="MENO DI 2"
  txt+=f"{etichetta} - {tname}: {med:.2f}\n"
  time.sleep(0.4)
 return txt

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
     last_id=u['update_id'];txt=u.get('message',{}).get('text','').lower();cid=u.get('message',{}).get('chat',{}).get('id')
     if 'spegni' in txt:is_paused=True;tg('PAUSA',cid,True)
     elif 'accendi' in txt or '/start' in txt:is_paused=False;tg('RIPRESO - MEDIA GOL ATTIVA',cid,True)
     elif txt in [k.lower() for k in LEAGUES.keys()]:
      for k,v in LEAGUES.items():
       if k.lower()==txt:tg(f'Calcolo {k}...',cid);tg(media(v,k),cid,True)
  except:pass
  time.sleep(2)

def get_stat(a,n):
 for s in a:
  if s.get('type')==n:
   try:return int(str(s.get('value') or 0).replace('%','').strip() or 0)
   except:return 0
 return 0

def live():
 tg('BOT V18 MEDIA GOL - PIU DI 2 / MENO DI 2 ATTIVO',keys=True)
 while True:
  try:
   if is_paused:time.sleep(30);continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:time.sleep(300);continue
   games=api('https://v3.football.api-sports.io/fixtures?live=all')
   if games=='LIMIT':time.sleep(3600);continue
   if not games:time.sleep(60);continue
   games=[g for g in games if g['league']['id'] in LEAGUES.values()]
   for g in games:
    fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
    if m is None:continue
    home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
    if 65<=m<=90 and fid not in av_s:
     st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
     sot=0
     if st and len(st)>=2:
      for s in st:
       for x in s['statistics']:
        if x['type']=='Shots on Goal':
         try:sot+=int(str(x['value']).replace('%','') or 0)
         except:pass
     if sot>=4:
      tg(f"GIOCALO {m}' {g['league']['country']} {home} {gh}-{ga} {away} Tiri:{sot}");av_s.add(fid);av_g[fid]=gh+ga
   for g in games:
    fid=g['fixture']['id']
    if fid in av_g:
     tot=g['goals']['home']+g['goals']['away']
     if tot>av_g[fid]:tg(f"GOAL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
   time.sleep(60)
  except Exception as e:print(e);time.sleep(15)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live,daemon=True).start()
if __name__=='__main__':
 app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
 
