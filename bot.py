import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_id=0;av_g={};av_s=set();pre=set();pre1=set();cache={}
# 33 NAZIONI COMPRESA TURCHIA
LEAGUES={'Serie A':135,'Serie B':136,'Serie C':138,'Inghilterra':39,'Championship':40,'Spagna':140,'Spagna 2':142,'Germania':78,'Germania 2':79,'Francia':61,'Francia 2':62,'Olanda':88,'Portogallo':94,'Belgio':144,'Scozia':179,'Austria':218,'Svizzera':207,'Danimarca':119,'Svezia':113,'Norvegia':103,'Turchia':203,'Grecia':197,'Polonia':106,'Cechia':345,'Croazia':210,'Serbia':286,'Romania':283,'Ungheria':271,'Ucraina':333,'Russia':235,'Cipro':318,'Bulgaria':172,'Irlanda':344}
app=Flask(__name__)
@app.route('/')
def home():return f'BOT V19.2 BOLLA 33 NAZIONI OK - {datetime.now(ITALY).strftime("%H:%M")}',200

TAST=json.dumps({
"keyboard":[
["Serie A","Serie B","Inghilterra"],
["Spagna","Germania","Francia"],
["Olanda","Portogallo","Belgio"],
["Austria","Svizzera","Turchia"],
["Svezia","Norvegia","Danimarca"],
["BOLLA EUROPA 33 NAZIONI"],
["BOLLA 20","TUTTA EUROPA"],
["ACCENDI","SPEGNI","STATUS"]
],
"resize_keyboard":True,"is_persistent":True
})

def tg(m,cid=None,keys=False):
 try:
  cid=cid or CHAT;base=f'https://api.telegram.org/bot{BOT}';pay={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if keys:pay['reply_markup']=TAST
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
  if med>2: etichetta="PIU' DI 2"
  else: etichetta="MENO DI 2"
  txt+=f"{etichetta} - {tname}: {med:.2f}\n"
  time.sleep(0.4)
 return txt

def crea_bolla():
 try:
  picks=[];quota=1.0
  BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly"]
  for gg in range(3):
   if len(picks)>=20: break
   giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
   fixtures=api(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
   if not fixtures: continue
   fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
   for p in fixtures:
    if len(picks)>=20: break
    # QUI PRENDE TUTTE LE 33 NAZIONI COMPRESA TURCHIA
    if p['league']['id'] not in LEAGUES.values(): continue
    if any(b.lower() in p["league"]["name"].lower() for b in BAN): continue
    fid=p["fixture"]["id"]
    dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
    if dt < datetime.now(ITALY): continue
    home=p['teams']['home']['name'];away=p['teams']['away']['name'];paese=p['league']['country'];lega=p['league']['name'];orario=dt.strftime("%H:%M")
    odds=api(f"https://v3.football.api-sports.io/odds?fixture={fid}")
    if not odds or odds=="LIMIT": continue
    if not odds[0].get("bookmakers"): continue
    try:
     over=None
     for bet in odds[0]["bookmakers"][0]["bets"]:
      if "Over/Under" not in bet["name"]: continue
      for v in bet["values"]:
       if "Over 0.5" in v["value"]:
        q=float(v["odd"])
        if 1.01 <= q <= 1.35: over=q; break
      if over: break
     if not over: continue
     quota=round(quota*over,2)
     picks.append(f"{orario} {giorno[5:10]} - {paese} - {lega}\n{home} vs {away}\nOver 0.5 @ {over}")
    except: continue
  if len(picks)<5: return f"Poche partite nelle 33 nazioni, trovate {len(picks)}"
  return f"BOLLA EUROPA 33 NAZIONI - Turchia inclusa\n{len(picks)} partite - Quota {quota:.2f}\n\n"+"\n\n".join(picks)+f"\n\nTOT {quota:.2f}"
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
     elif 'accendi' in txt or '/start' in txt:is_paused=False;tg('RIPRESO - BOLLA 33 NAZIONI ATTIVA',cid,True)
     elif 'status' in txt:tg(f"STATUS {'PAUSA' if is_paused else 'ATTIVO'} | Leghe: {len(LEAGUES)} con Turchia",cid,True)
     elif 'bolla' in txt:tg('Creo BOLLA EUROPA 33 NAZIONI (Turchia inclusa)... 40 sec',cid);tg(crea_bolla(),cid,True)
     elif txt in [k.lower() for k in LEAGUES.keys()]:
      for k,v in LEAGUES.items():
       if k.lower()==txt:tg(f'Calcolo {k}...',cid);tg(media(v,k),cid,True);break
  except:pass
  time.sleep(2)

def get_stat(a,n):
 for s in a:
  if s.get('type')==n:
   try:return int(str(s.get('value') or 0).replace('%','').strip() or 0)
   except:return 0
 return 0

def live():
 tg('BOT V19.2 BOLLA 33 NAZIONI + LIVE ATTIVO',keys=True)
 while True:
  try:
   if is_paused:time.sleep(30);continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:time.sleep(300);continue
   if now.hour==0 and now.minute<5: av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear()
   games=api('https://v3.football.api-sports.io/fixtures?live=all')
   if games=='LIMIT':time.sleep(3600);continue
   if not games:time.sleep(60);continue
   games=[g for g in games if g['league']['id'] in LEAGUES.values()]
   for g in games:
    fid=g['fixture']['id'];st=g['fixture']['status']['short'];m=g['fixture']['status']['elapsed']
    if m is None or fid in av_s:continue
    home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
    pref=f"{g['league']['country']} - {g['league']['name']}"
    def tiri():
     d=cache.get(fid)
     if not d or time.time()-d.get('time',0)>180:
      s=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
      if s and len(s)>=2:
       sot=get_stat(s[0]['statistics'],'Shots on Goal')+get_stat(s[1]['statistics'],'Shots on Goal')
       cache[fid]={'sot':sot,'time':time.time()};time.sleep(0.4);return sot
      return d.get('sot',0) if d else 0
     return d.get('sot',0)
    if st=='HT' and fid not in pre1:
     so=tiri()
     if so>=3:tg(f"FINE 1T {pref} | Tiri:{so} | {home} {gh}-{ga} {away}");pre1.add(fid)
    if 46<=(m or 0)<=69 and fid not in pre:
     so=tiri()
     if so>=5:tg(f"PREPARATI {m}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT");pre.add(fid)
    if 65<=(m or 0)<=92:
     so=tiri()
     if so>=4 and fid not in av_s:
      sq=home if gh<=ga else away
      tg(f"GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}");av_s.add(fid);av_g[fid]=gh+ga
   for g in games:
    fid=g['fixture']['id']
    if fid in av_g:
     tot=g['goals']['home']+g['goals']['away']
     if tot>av_g[fid]:tg(f"GOAL VINTO! {g['league']['country']} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
   time.sleep(60)
  except Exception as e:print(e);time.sleep(15)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live,daemon=True).start()
if __name__=='__main__':
 app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
