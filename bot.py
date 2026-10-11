import os,time,requests,threading,json
from flask import Flask
BOT=os.getenv('BOT_TOKEN')
CHAT=os.getenv('CHAT_ID')
KEY=os.getenv('API_FOOTBALL_KEY')
is_paused=False
last_id=0
pre=set()
gio=set()
cache={}

def youth(n):
 if not n: return False
 x=n.lower()
 for k in ['u19','u21','u23','women',' female']:
  if k in x: return True
 return False

app=Flask(__name__)
@app.route('/')
def home(): return "V33.52 OK",200

K1=json.dumps({"keyboard":[[{"text":"MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"STATUS"},{"text":"TEST LIVE"}],[{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})

def tg(m,cid=None,reply=None):
 try:
  cid=cid or CHAT
  d={'chat_id':cid,'text':m}
  if reply: d['reply_markup']=json.loads(reply) if isinstance(reply,str) else reply
  requests.post('https://api.telegram.org/bot'+BOT+'/sendMessage',json=d,timeout=20)
 except: pass

def api(ep):
 try:
  r=requests.get('https://v3.football.api-sports.io/'+ep,headers={'x-apisports-key':KEY},timeout=30)
  if r.status_code==429: return 'LIMIT'
  return r.json().get('response',[])
 except: return []

def get_sot(fid):
 now=time.time()
 if fid in cache:
  ts,v=cache[fid]
  if now-ts<120: return v
 st=api('fixtures/statistics?fixture='+str(fid))
 if st=='LIMIT': return -1
 if not st: return 0
 s=0
 for a in st:
  for b in a['statistics']:
   if b['type']=='Shots on Goal':
    try: s+=int(str(b['value'] or 0))
    except: pass
 cache[fid]=(now,s)
 return s

def poll():
 global is_paused,last_id
 try: requests.get('https://api.telegram.org/bot'+BOT+'/deleteWebhook?drop_pending_updates=true',timeout=10)
 except: pass
 while True:
  try:
   r=requests.get('https://api.telegram.org/bot'+BOT+'/getUpdates?offset='+str(last_id+1)+'&timeout=20',timeout=30).json()
   for u in r.get('result',[]):
    last_id=u['update_id']
    txt=(u.get('message',{}).get('text') or '').strip().upper()
    cid=u.get('message',{}).get('chat',{}).get('id')
    if 'MENU' in txt: tg('MENU V33.52',cid,reply=K2)
    elif 'CHIUDI' in txt: tg('Chiuso',cid,reply=K1)
    elif 'STATUS' in txt:
     g=api('fixtures?live=all')
     tg(f"Live:{len(g) if g!='LIMIT' and g else 0} PRE:{len(pre)} GIO:{len(gio)}",cid,reply=K1)
    elif 'TEST' in txt:
     g=api('fixtures?live=all')
     tg(f"Vedo {len(g)} live - 5 esempi con nazione:",cid,reply=K1)
     c=0
     for x in g[:25]:
      if youth(x['league']['name']): continue
      m=x['fixture']['status']['elapsed'] or 0
      if m<5 or m>70: continue
      s=get_sot(x['fixture']['id'])
      tg(f"{x['league']['country']} {x['league']['name']} - {x['teams']['home']['name']} {x['goals']['home'] or 0}-{x['goals']['away'] or 0} {x['teams']['away']['name']} - {s} tiri {m}m",cid,reply=K1)
      c+=1
      time.sleep(1)
      if c>=5: break
    elif 'SPEGNI' in txt: is_paused=True; tg('PAUSA',cid,reply=K1)
    elif 'ACCENDI' in txt: is_paused=False; tg('ATTIVO',cid,reply=K1)
  except: pass
  time.sleep(1)

def live():
 tg('V33.52 ATTIVO - 3=PREPARATI / 5=GIOCALO solo fino 70m',reply=K1)
 idx=0
 while True:
  try:
   if is_paused: time.sleep(20); continue
   games=api('fixtures?live=all')
   if games=='LIMIT' or not games: time.sleep(90); continue
   if idx>=len(games): idx=0
   batch=games[idx:idx+12]
   idx+=12
   for g in batch:
    try:
     if youth(g['league']['name']): continue
     fid=g['fixture']['id']
     m=g['fixture']['status']['elapsed']
     if m is None or m<10 or m>70: continue # <--- BLOCCO AL 70°
     if fid in gio: continue
     sot=get_sot(fid)
     if sot==-1 or sot==0: time.sleep(1); continue
     country=g['league']['country']
     league=g['league']['name']
     h=g['teams']['home']['name']
     a=g['teams']['away']['name']
     gh=g['goals']['home'] or 0
     ga=g['goals']['away'] or 0
     base=f"{country} {league} - {h} {gh}-{ga} {a} - {sot} tiri {m}m"
     if sot>=3 and fid not in pre:
      tg(f"PREPARATI {base}",reply=K1)
      pre.add(fid)
     if sot>=5 and fid not in gio:
      tg(f"GIOCALO {base}",reply=K1)
      gio.add(fid)
     time.sleep(1.1)
    except: continue
   time.sleep(12)
  except: time.sleep(10)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live,daemon=True).start()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
