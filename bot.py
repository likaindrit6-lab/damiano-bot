import os, time, requests, threading, json
from flask import Flask
from datetime import datetime, timezone, timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2));last_id=0

TOP33={
"Italia":135,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,
"Portogallo":94,"Olanda":88,"Belgio":144,"Turchia":203,"Scozia":179,
"Austria":218,"Svizzera":207,"Danimarca":119,"Svezia":113,"Norvegia":103,
"Polonia":106,"Rep Ceca":110,"Croazia":210,"Serbia":286,"Grecia":197,
"Romania":283,"Ungheria":271,"Bulgaria":172,"Slovacchia":334,"Slovenia":373,
"Cipro":318,"Israele":383,"Ucraina":333,"Bielorussia":116,"Irlanda":84,
"Irlanda Nord":410,"Galles":1107,"Islanda":108
}
LEAGUES={'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}

app=Flask(__name__)
@app.route('/')
def home(): return 'V56 33 NAZIONI VERE OK',200
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
  if not d: return "1X @ 1.15"
  for bk in d[0].get('bookmakers',[])[:2]:
   for bet in bk.get('bets',[]):
    if 'Double Chance' in bet['name']:
     best=None;odd=10.0
     for v in bet['values']:
      try:
       o=float(v['odd'])
       if o<odd: odd=o;best=v['value']
      except: continue
     if best:
      if 'Home/Draw' in best: return f"1X @ {odd:.2f}"
      if 'Draw/Away' in best: return f"X2 @ {odd:.2f}"
      if 'Home/Away' in best: return f"12 @ {odd:.2f}"
 except: pass
 return "1X @ 1.20"

def run_bolla(cid=None):
 sel=[]
 for paese, lid in TOP33.items():
  found=False
  for d in range(0,15):
   date=(datetime.now(ITALY)+timedelta(days=d)).strftime("%Y-%m-%d")
   data=api(f'https://v3.football.api-sports.io/fixtures?date={date}&league={lid}&season=2024')
   if data:
    f=data[0]
    ora=f['fixture']['date'][11:16]
    dc=get_dc(f['fixture']['id'])
    sel.append(f"{f['fixture']['date'][:10]} {ora} {f['teams']['home']['name']} vs {f['teams']['away']['name']} -> {dc} ({paese})")
    found=True;time.sleep(0.2);break
  if not found:
   sel.append(f"RINVIATA - {paese} (sosta)")
  if len(sel)>=33: break
 tg(f"BOLLA EUROPA 33 NAZIONI VERE\n{len(sel)} partite\n\n"+"\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def run_doppia(cid=None):
 out=[]
 for d in range(0,3):
  date=(datetime.now(ITALY)+timedelta(days=d)).strftime("%Y-%m-%d")
  data=api(f'https://v3.football.api-sports.io/fixtures?date={date}&timezone=Europe/Rome')
  for f in data:
   dc=get_dc(f['fixture']['id'])
   out.append(f"{f['fixture']['date'][11:16]} {f['teams']['home']['name']} vs {f['teams']['away']['name']} -> {dc}");time.sleep(0.15)
   if len(out)>=20: break
  if len(out)>=20: break
 tg(f"DOPPIA 90% {len(out)}\n\n"+"\n".join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,True)

def media(lid,name):
 txt=name.upper()+f" {datetime.now(ITALY).strftime('%d/%m')}\nGOAL + CORNER\n\n"
 teams=api(f'https://v3.football.api-sports.io/teams?league={lid}&season=2024')
 for t in teams[:10]:
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
  txt+=f"{tname}: {gf}F/{gs}S Med {tot/c:.2f} Corn ~5\n";time.sleep(0.2)
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
     last_id=u['update_id'];m=u.get('message',{});txt=(m.get('text') or '').strip();low=txt.lower();cid=m.get('chat',{}).
