import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False;last_update_id=0;av_g={};av_s=set();pre=set();pre1=set();cache={};tripla_coda=[];ultimo_invio_tripla=time.time()

TOP33={"Italia":135,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,"Portogallo":94,"Olanda":88,"Belgio":144,"Turchia":203,"Scozia":179,"Austria":218,"Svizzera":207,"Danimarca":119,"Svezia":113,"Norvegia":103,"Polonia":106,"Rep Ceca":110,"Croazia":210,"Serbia":286,"Grecia":197,"Romania":283,"Ungheria":271,"Bulgaria":172,"Slovacchia":334,"Slovenia":373,"Cipro":318,"Israele":383,"Ucraina":333,"Bielorussia":116,"Irlanda":84,"Irlanda Nord":410,"Galles":1107,"Islanda":108}
ALLOWED=set(list(TOP33.values())+[135,136,39,40,140,78,61,88,94,144,203])

try:base=f"https://api.telegram.org/bot{BOT_TOKEN}";requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except:pass
app=Flask(__name__)
@app.route('/')
def home():s="PAUSA" if is_paused else "ATTIVO";return f"V69 FINAL - {s}",200
def run_flask():
 from waitress import serve;p=int(os.environ.get("PORT",10000));serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()
TASTIERA_JSON=json.dumps({"keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,cid=None,k=False):
 try:
  cid=cid or CHAT_ID;base=f"https://api.telegram.org/bot{BOT_TOKEN}";url=base+"/sendMessage"
  if len(m)>3900:
   for i in range(0,len(m),3900):pay={"chat_id":cid,"text":m[i:i+3900],"parse_mode":"HTML"};requests.post(url,json=pay,timeout=25)
  else:pay={"chat_id":cid,"text":m,"parse_mode":"HTML"};
  if k:pay["reply_markup"]=json.loads(TASTIERA_JSON)
  requests.post(url,json=pay,timeout=25)
 except:pass

def api_get(u):
 try:r=requests.get(u,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30);return r.json().get("response",[]) if r.status_code!=429 else "LIMIT"
 except:return []
def get_stat(a,n):
 for s in a:
  if s.get('type')==n:
   try:return int(str(s.get('value') or 0).replace('%','') or 0)
   except:return 0
 return 0
def get_flag(p):m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷"};return m.get(p,f"[{p}]")

def crea_bolla():
 try:
  OGGI=datetime.now(ITALY).strftime("%Y-%m-%d");fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}");fixtures=[g for g in fixtures if g['league']['id'] in ALLOWED]
  if not fixtures:return f"Nessuna partita oggi {OGGI} - solo Europa"
  picks=[];quota_tot=1.0;fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
  for p in fixtures:
   if len(picks)>=10 or quota_tot>=3.35:break
   fid=p["fixture"]["id"];dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
   if dt<datetime.now(ITALY):continue
   home=p['teams']['home']['name'];away=p['teams']['away']['name'];paese=p['league']['country'];lega=p['league']['name'];orario=dt.strftime("%H:%M")
   odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
   if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"):continue
   best=None
   for bet in odds[0]["bookmakers"][0]["bets"]:
    if "First Half" in bet["name"] or "Corners" in bet["name"] or "Cards" in bet["name"]:continue
    for v in bet["values"]:
     try:
      q=float(v["odd"])
      if 1.08<=q<=1.30:
       if best is None or q>best["q"]:best={"m":bet["name"],"e":v["value"],"q":q}
     except:continue
   if not best or quota_tot*best["q"]>3.45:continue
   m_name=best["m"];m_val=best["e"]
   if "Match Winner" in m_name:txt="1" if "Home" in m_val else "2" if "Away" in m_val else "X"
   elif "Double Chance" in m_name:txt=m_val.replace("Home/Draw","1X").replace("Draw/Away","X2").replace("Home/Away","12")
   else:txt=f"{m_name}: {m_val}"
   quota_tot*=best["q"];q_finale=best["q"]*1.25
   picks.append(f"🕐 {orario}\n📍 {paese} - {lega}\n{home} vs {away}\n👉 {txt} + Multigol 1-5 @ {q_finale:.2f}")
  if len(picks)<5:return f"Poche partite oggi, trovate {len(picks)}"
  return f"🔥 BOLLA {OGGI} - Quota {quota_tot:.2f}\n\n"+"\n\n".join(picks)
 except Exception as e:return f"Errore bolla: {e}"

def poll_commands():
 global is_paused,last_update_id
 while True:
  try:
   base=f"https://api.telegram.org/bot{BOT_TOKEN}";url=base+f"/getUpdates?offset={last_update_id+1}&timeout=25";r=requests.get(url,timeout=35).json()
   if r.get("ok"):
    for upd in r.get("result",[]):
     last_update_id=upd["update_id"];msg=upd.get("message",{});txt=(msg.get("text") or "").lower().strip();cid=msg.get("chat",{}).get("id")
     if "spegni" in txt:is_paused=True;tg("🛑 PAUSA",cid,True)
     elif "accendi" in txt or txt=="/start":is_paused=False;tg("✅ RIPRESO",cid,True)
     elif "status" in txt:ora=datetime.now(ITALY).strftime('%H:%M');st="PAUSA" if is_paused else "ATTIVO";tg(f"📊 {st} | {ora}",cid,True)
     elif "bolla" in txt:tg("⏳ Creo bolla Europa...",cid);tg(crea_bolla(),cid,True)
  except:pass
  time.sleep(2)
threading.Thread(target=poll_commands,daemon=True).start()

while True:
 try:
  if is_paused:time.sleep(30);continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
   time.sleep(300);continue
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT" or not live:time.sleep(60);continue
  live=[g for g in live if g['league']['id'] in ALLOWED]
  if time.time()-ultimo_invio_tripla>=3600 and len(tripla_coda)>=2:
   txt=f"🔥🔥🔥 TRIPLA ORARIA {now.strftime('%H:%M')} 🔥🔥🔥\n\n"
   for p in tripla_coda[:3]:txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} Corner:{p['corn']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
   tg(txt);tripla_coda=tripla_coda[3:];ultimo_invio_tripla=time.time()
  for g in live:
   fid=g["fixture"]["id"];m=g["fixture"]["status"]["elapsed"];st=g["fixture"]["status"]["short"]
   if m is None or fid in av_s:continue
   home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
   paese=g['league']['country'];lega=g['league']['name'];flag=get_flag(paese);pref=f"{flag} {paese.upper()} - {lega}"
   def stats_live():
    d=cache.get(fid)
    if not d or time.time()-d.get('time',0)>180:
     s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if s and len(s)>=2:
      sot=get_stat(s[0]['statistics'],'Shots on Goal')+get_stat(s[1]['statistics'],'Shots on Goal')
      corn=get_stat(s[0]['statistics'],'Corner Kicks')+get_stat(s[1]['statistics'],'Corner Kicks')
      cache[fid]={'sot':sot,'corn':corn,'time':time.time()};time.sleep(0.4);return sot,corn
     return d.get('sot',0),d.get('corn',0) if d else (0,0)
    return d.get('sot',0),d.get('corn',0)
   if st=="HT" and fid not in pre1:
    so,co=stats_live()
    if so>=3:tg(f"⏸️ FINE 1T {pref} | Tiri:{so} | Corner:{co} | {home} {gh}-{ga} {away}");pre1.add(fid)
   if 46<=(m or 0)<=69 and fid not in pre:
    so,co=stats_live()
    if so>=5 or co>=6:tg(f"🔔 PREPARATI {m}' {pref} | Tiri:{so} | Corner:{co} | {home} {gh}-{ga} {away} | NEXT");pre.add(fid)
   if 65<=(m or 0)<=92:
    so,co=stats_live()
    if (so>=4 or co>=7) and fid not in av_s:
     sq=home if gh<=ga else away;tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} | Corner:{co} | {home} {gh}-{ga} {away} | NEXT {sq}");av_s.add(fid);av_g[fid]=gh+ga
     if not any(x['fid']==fid for x in tripla_coda):tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':m,'sot':so,'corn':co,'home':home,'away':away,'gh':gh,'ga':ga})
  for g in live:
   fid=g["fixture"]["id"]
   if fid in av_g:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>av_g[fid]:flag=get_flag(g['league']['country']);tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
  time.sleep(60)
 except:time.sleep(15)
