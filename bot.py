import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_id=0;av_g={};av_s=set();pre=set();pre1=set();cache={}
LEAGUES={'Serie A':135,'Serie B':136,'Serie C':138,'Inghilterra':39,'Championship':40,'Spagna':140,'Spagna 2':142,'Germania':78,'Germania 2':79,'Francia':61,'Francia 2':62,'Olanda':88,'Portogallo':94,'Belgio':144,'Scozia':179,'Austria':218,'Svizzera':207,'Danimarca':119,'Svezia':113,'Norvegia':103,'Turchia':203,'Grecia':197,'Polonia':106,'Cechia':345,'Croazia':210,'Serbia':286,'Romania':283,'Ungheria':271,'Ucraina':333,'Russia':235,'Cipro':318,'Bulgaria':172,'Irlanda':344}
app=Flask(__name__)
@app.route('/')
def home():return f'BOT V21.2 TASTIERA FIX - {datetime.now(ITALY).strftime("%H:%M")}',200

# FIX TASTIERA CHE SI ABBASSA DA SOLA
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["BOLLA 20","STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True,"is_persistent":False,"one_time_keyboard":True,"input_field_placeholder":"Clicca qui per menu..."})

def tg(m,cid=None,keys=False):
 try:
  cid=cid or CHAT;base=f'https://api.telegram.org/bot{BOT}';pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys:pay['reply_markup']=json.loads(TAST)
  requests.post(base+'/sendMessage',json=pay,timeout=25)
 except:pass

def chiudi(cid):
 try:
  base=f'https://api.telegram.org/bot{BOT}'
  requests.post(base+'/sendMessage',json={'chat_id':cid,'text':'Tastiera chiusa - schermo libero ✅\nClicca ☰ in basso per riaprirla','reply_markup':{"remove_keyboard":True}},timeout=10)
 except:pass

def api(url):
 try:
  r=requests.get(url,headers={'x-apisports-key':KEY},timeout=30)
  if r.status_code==429:return 'LIMIT'
  return r.json().get('response',[])
 except:return []

def media(lid,name):
 txt=f'{name.upper()} - MEDIA ULTIME 10\n{datetime.now(ITALY).strftime("%d/%m %H:%M")}\n\n'
 teams=api(f'https://v3.football.api-sports.io/teams?league={lid}&season=2024')
 if not teams:return 'Errore API'
 for t in teams[:14]:
  tid=t['team']['id'];tname=t['team']['name']
  last=api(f"https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024")
  if not last or last=='LIMIT':time.sleep(0.5);continue
  tot=0;c=0
  for p in last:
   gh=p['goals']['home'];ga=p['goals']['away']
   if gh is None:continue
   tot+=gh+ga;c+=1
  if c==0:continue
  med=tot/c
  et="PIU' DI 2" if med>2 else "MENO DI 2"
  txt+=f"{et} - {tname}: {med:.2f}\n";time.sleep(0.4)
 return txt

def crea_doppia():
 try:
  txt=f"DOPPIA ALTA % - TUTTE LE 33 NAZIONI SETTIMANA\n{datetime.now(ITALY).strftime('%d/%m')}\n\n"
  ris=[]
  BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly"]
  for gg in range(7):
   giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
   fixtures=api(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
   if not fixtures or fixtures=='LIMIT':continue
   for p in fixtures:
    if p['league']['id'] not in LEAGUES.values():continue
    if any(b.lower() in p["league"]["name"].lower() for b in BAN):continue
    fid=p["fixture"]["id"]
    dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
    if dt < datetime.now(ITALY):continue
    if len(ris)>=25:break
    hid=p['teams']['home']['id'];aid=p['teams']['away']['id']
    home=p['teams']['home']['name'];away=p['teams']['away']['name']
    h_last=api(f"https://v3.football.api-sports.io/fixtures?team={hid}&last=10&season=2024");time.sleep(0.35)
    a_last=api(f"https://v3.football.api-sports.io/fixtures?team={aid}&last=10&season=2024");time.sleep(0.35)
    if not h_last or not a_last:continue
    hw=hd=hl=0
    for m in h_last:
     if m['goals']['home'] is None:continue
     is_home=m['teams']['home']['id']==hid
     w=m['teams']['home']['winner'] if is_home else m['teams']['away']['winner']
     d=m['teams']['home']['winner']==False and m['teams']['away']['winner']==False
     if w==True:hw+=1
     elif d:hd+=1
     else:hl+=1
    aw=ad=al=0
    for m in a_last:
     if m['goals']['home'] is None:continue
     is_home=m['teams']['home']['id']==aid
     w=m['teams']['home']['winner'] if is_home else m['teams']['away']['winner']
     d=m['teams']['home']['winner']==False and m['teams']['away']['winner']==False
     if w==True:aw+=1
     elif d:ad+=1
     else:al+=1
    p1x = (hw+hd)*10
    px2 = (aw+ad)*10
    p12 = 100 - ((hd+ad)/2*10)
    p1x = round((p1x + (100-aw*10))/2)
    px2 = round((px2 + (100-hw*10))/2)
    if p1x>=px2 and p1x>=p12: best=f"1X {p1x}%"; perc=p1x
    elif px2>=p1x and px2>=p12: best=f"X2 {px2}%"; perc=px2
    else: best=f"12 {p12:.0f}%"; perc=p12
    if perc>=60:
     ris.append((perc,f"{dt.strftime('%d/%m %H:%M')} {p['league']['country']} {home} vs {away} -> {best}"))
  ris=sorted(ris,key=lambda x:x[0],reverse=True)
  if not ris:return "Nessuna partita trovata"
  for _,r in ris: txt+=r+"\n\n"
  return txt[:3900]
 except Exception as e: return f"Errore doppia: {e}"

def crea_bolla():
 try:
  picks=[];quota=1.0;BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly"]
  for gg in range(3):
   if len(picks)>=20:break
   giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
   fixtures=api(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
   if not fixtures:continue
   fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
   for p in fixtures:
    if len(picks)>=20:break
    if p['league']['id'] not in LEAGUES.values():continue
    if any(b.lower() in p["league"]["name"].lower() for b in BAN):continue
    fid=p["fixture"]["id"];dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
    if dt < datetime.now(ITALY):continue
    home=p['teams']['home']['name'];away=p['teams']['away']['name'];paese=p['league']['country'];lega=p['league']['name'];orario=dt.strftime("%H:%M")
    odds=api(f"https://v3.football.api-sports.io/odds?fixture={fid}")
    if not odds or odds=="LIMIT":continue
    if not odds[0].get("bookmakers"):continue
    try:
     over=None
     for bet in odds[0]["bookmakers"][0]["bets"]:
      if "Over/Under" not in bet["name"]:continue
      for v in bet["values"]:
       if "Over 0.5" in v["value"]:
        q=float(v["odd"])
        if 1.01 <= q <= 1.35: over=q;break
      if over:break
     if not over:continue
     quota=round(quota*over,2)
     picks.append(f"{orario} {giorno[5:10]} - {paese} - {lega}\n{home} vs {away}\nOver 0.5 @ {over}")
    except:continue
  if len(picks)<5:return f"Poche partite, trovate {len(picks)}"
  return f"BOLLA EUROPA 33 NAZIONI - Quota {quota:.2f}\n\n"+"\n\n".join(picks)+f"\n\nTOT {quota:.2f}"
 except Exception as e: return f"Errore bolla: {e}"

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
     last_id=u['update_id'];txt_raw=u.get('message',{}).get('text','');txt=txt_raw.lower().strip();cid=u.get('message',{}).get('chat',{}).get('id')
     if 'spegni' in txt:is_paused=True;tg('PAUSA',cid,True)
     elif 'accendi' in txt or '/start' in txt:is_paused=False;tg('RIPRESO - DOPPIA REALE ATTIVA',cid,True)
     elif 'status' in txt:tg(f"STATUS {'PAUSA' if is_paused else 'ATTIVO'}",cid,True)
     elif 'doppia' in txt:tg('Calcolo TUTTE le partite 33 nazioni...
