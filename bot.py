import os, time, requests, threading, json
from flask import Flask
from datetime import datetime, timezone, timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));last_id=0
LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}
app=Flask(__name__)
@app.route('/')
def home(): return 'V52 OK',200
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA 90%"],["BOLLA EUROPA 33 NAZIONI"],["STATUS"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False):
 try:
  cid=cid or CHAT
  b='https://api.telegram.org/bot'+BOT;pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys: pay['reply_markup']=json.loads(TAST)
  requests.post(b+'/sendMessage',json=pay,timeout=20)
 except: pass
def api(u):
 try:
  r=requests.get(u,headers={'x-apisports-key':KEY},timeout=30)
  return r.json().get('response',[])
 except: return []
def get_dc(fid):
 try:
  d=api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
  if not d: return None
  for bk in d[0].get('bookmakers',[])[:3]:
   for bet in bk.get('bets',[]):
    if 'Double Chance' in bet['name']:
     best=None;odd=10.0
     for v in bet['values']:
      try:
       o=float(v['odd'])
       if o<odd: odd=o;best=v['value']
      except: continue
     if best:
      prob=int(100/odd) if odd else 0
      if 'Home/Draw' in best: return f"1X @ {odd:.2f} ({prob}%)",prob
      if 'Draw/Away' in best: return f"X2 @ {odd:.2f} ({prob}%)",prob
      if 'Home/Away' in best: return f"12 @ {odd:.2f} ({prob}%)",prob
 except: pass
 return None
def fixtures(days):
 date=(datetime.now(ITALY)+timedelta(days=days)).strftime("%Y-%m-%d")
 return api(f'https://v3.football.api-sports.io/fixtures?date={date}&timezone=Europe/Rome')
def run_bolla(cid=None):
 sel=[];seen=set()
 for d in [0,1,2]:
  data=fixtures(d)
  for f in data:
   if len(sel)>=33: break
   key=f['league']['id']
   if key in seen: continue
   ora=f['fixture']['date'][11:16]
   home=f['teams']['home']['name'];away=f['teams']['away']['name']
   res=get_dc(f['fixture']['id'])
   dc=res[0] if res else "1X @ 1.20"
   if res: time.sleep(0.2)
   sel.append(f"{ora} {home} vs {away} -> {dc} ({f['league']['country']})");seen.add(key)
  if len(sel)>=33: break
 tg(f"BOLLA {len(sel)} NAZIONI (3 giorni)\n\n"+"\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)
def run_doppia(cid=None):
 out=[]
 for d in [0,1,2]:
  for f in fixtures(d):
   res=get_dc(f['fixture']['id'])
   if not res or res[1]<80: continue
   out.append((res[1],f"{f['fixture']['date'][11:16]} {f['teams']['home']['name']} vs {f['teams']['away']['name']} -> {res[0]}"));time.sleep(0.2)
 if out:
  out.sort(key=lambda x:x[0],reverse=True)
  tg(f"DOPPIA 90% {len(out)}\n\n"+"\n".join([f"{i+1}. {m}" for i,(p,m) in enumerate(out[:20])]),cid,True)
 else: tg("Nessuna DOPPIA 90%",cid,True)
def media(lid,name):
 txt=name.upper()+"\n"+datetime.now(ITALY).strftime("%d/%m %H:%M")+"\n\n"
 teams=api(f'https://v3.football.api-sports.io/teams?league={lid}&season=2024')
 for t in teams[:12]:
  tid=t['team']['id'];tname=t['team']['name']
  last=api(f'https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024')
  gf=gs=tot=c=0
  for p in last:
   gh=p['goals']['home'];ga=p['goals']['away']
   if gh is None: continue
   if p['teams']['home']['id']==tid: gf+=gh;gs+=ga
   else: gf+=ga;gs+=gh
   tot+=gh+ga;c+=1
  if c==0: continue
  txt+=f"{tname}: {gf}F/{gs}S Diff {gf-gs:+} Med {tot/c:.2f}\n";time.sleep(0.2)
 return txt
def poll():
 global last_id
 try:
  if BOT: requests.get('https://api.telegram.org/bot'+BOT+'/deleteWebhook?drop_pending_updates=true',timeout=10)
 except: pass
 while True:
  try:
   base='https://api.telegram.org/bot'+BOT
   r=requests.get(base+f'/getUpdates?offset={last_id+1}&timeout=20',timeout=30).json()
   if r.get('ok'):
    for u in r.get('result',[]):
     last_id=u['update_id'];m=u.get('message',{});txt=(m.get('text') or '').strip();low=txt.lower();cid=m.get('chat',{}).get('id')
     if not txt: continue
     if 'doppia' in low: run_doppia(cid)
     elif 'bolla' in low: run_bolla(cid)
     elif 'status' in low: tg('BOT V52 OK - 3 GIORNI',cid,True)
     else:
      for k in LEAGUES:
       if k.lower()==low: tg(media(LEAGUES[k],k),cid,True)
  except: pass
  time.sleep(2)
threading.Thread(target=poll,daemon=True).start()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
