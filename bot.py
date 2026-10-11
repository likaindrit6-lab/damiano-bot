import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN')
CHAT=os.getenv('CHAT_ID')
KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_id=0
sot_sent=set()
gol_tracker={}
gol_fatto=set()
pt_sent=set()
def youth(n):
 if not n: return False
 x=n.lower()
 for k in ['u19','u21','u23','u17','women',' w','female','youth']:
  if k in x: return True
 return False
app=Flask(__name__)
@app.route('/')
def home():
 return "BOT V33.43 FIX OK",200
K1=json.dumps({"keyboard":[[{"text":"MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"CAMPIONATI"}],[{"text":"CORNER"},{"text":"LIVE @3+"}],[{"text":"DOPPIA"},{"text":"BOLLA 33"}],[{"text":"ESATTI"}],[{"text":"STATUS"},{"text":"TEST LIVE"}],[{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})
def tg(m,cid=None,reply=None):
 try:
  cid=cid or CHAT
  url='https://api.telegram.org/bot'+BOT+'/sendMessage'
  data={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if reply: data['reply_markup']=json.loads(reply) if isinstance(reply,str) else reply
  requests.post(url,json=data,timeout=25)
 except: pass
def api_call(ep):
 try:
  base='https://v3.football.api-sports.io/'
  r=requests.get(base+ep,headers={'x-apisports-key':KEY},timeout=30)
  if r.status_code==429: return 'LIMIT'
  return r.json().get('response',[])
 except: return []
def get_sot(fid):
 try:
  st=api_call('fixtures/statistics?fixture='+str(fid))
  if not st or st=='LIMIT' or len(st)<2: return 0
  sot=0
  for s in st:
   for x in s['statistics']:
    if x['type']=='Shots on Goal':
     v=x['value']
     if v is None: continue
     sot+=int(str(v))
  return sot
 except: return 0
def poll():
 global is_paused,last_id
 try: requests.get('https://api.telegram.org/bot'+BOT+'/deleteWebhook?drop_pending_updates=true',timeout=10)
 except: pass
 while True:
  try:
   u='https://api.telegram.org/bot'+BOT+'/getUpdates?offset='+str(last_id+1)+'&timeout=20'
   r=requests.get(u,timeout=35).json()
   if r.get('ok'):
    for upd in r.get('result',[]):
     last_id=upd['update_id']
     msg=upd.get('message',{})
     txt=(msg.get('text') or '').strip()
     cid=msg.get('chat',{}).get('id')
     if not txt: continue
     up=txt.upper()
     if 'MENU' in up and 'CHIUDI' not in up:
      tg('MENU V33.43:',cid,reply=K2)
      continue
     if 'CHIUDI' in up:
      tg('Chiuso',cid,reply=K1)
      continue
     if 'STATUS' in up:
      games=api_call('fixtures?live=all')
      cnt=len(games) if games!='LIMIT' and games else 0
      tg('Live:'+str(cnt),cid,reply=K1)
      continue
     if 'TEST' in up:
      games=api_call('fixtures?live=all')
      tg('Vedo '+str(len(games) if games!='LIMIT' else 0)+' live',cid,reply=K1)
      continue
     if 'SPEGNI' in up:
      is_paused=True
      tg('PAUSA',cid,reply=K1)
      continue
     if 'ACCENDI' in up:
      is_paused=False
      tg('ATTIVO',cid,reply=K1)
      continue
  except: pass
  time.sleep(1)
def live_loop():
 tg('V33.43 FIX GA ATTIVO',reply=K1)
 while True:
  try:
   if is_paused:
    time.sleep(30)
    continue
   games=api_call('fixtures?live=all')
   if games=='LIMIT':
    time.sleep(3600)
    continue
   if not games:
    time.sleep(60)
    continue
   for g in games:
    try:
     if youth(g['league']['name']): continue
     fid=g['fixture']['id']
     m=g['fixture']['status']['elapsed']
     if m is None or m>85 or m<5: continue
     h=g['teams']['home']['name']
     a=g['teams']['away']['name']
     gh=g['goals']['home'] or 0
     ga=g['goals']['away'] or 0
     tot=gh+ga
     sot=get_sot(fid)
     if sot==0 or tot>sot: continue
     if fid not in pt_sent and m<=50 and sot>=3:
      tg('PRIMO TEMPO '+h+' '+str(gh)+'-'+str(ga)+' '+a+' '+str(sot)+' TIRI '+str(m)+'m',reply=K1)
      pt_sent.add(fid)
     if fid not in sot_sent and sot>=5:
      tg('GIOCALO! '+h+' '+str(gh)+'-'+str(ga)+' '+a+' '+str(sot)+' TIRI '+str(m)+'m',reply=K1)
      sot_sent.add(fid)
      gol_tracker[fid]=tot
     if fid in sot_sent and fid not in gol_fatto and tot>gol_tracker.get(fid,0):
      tg('GOAL! '+h+' '+str(gh)+'-'+str(ga)+' '+a,reply=K1)
      gol_fatto.add(fid)
    except: continue
   time.sleep(60)
  except: time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__':
 app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
