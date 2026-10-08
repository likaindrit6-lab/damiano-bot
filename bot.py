import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g={};av_s=set();pre=set();pre1=set();cache={}

try:
 requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home(): return "BOT V21 FIXATO",200

def run_flask():
 from waitress import serve
 serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

TAST=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BLASONATE LUN-DOM","PARTITE OGGI"],["SCHEDINA ORA","UNDER","TOKEN"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,cid=None,con_tastiera=True):
 try:
  url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload={"chat_id":str(cid or CHAT_ID),"text":m,"parse_mode":"HTML"}
  if con_tastiera:
   payload["reply_markup"]=TAST
  requests.post(url,json=payload,timeout=20)
 except: pass

def api_get(u):
 try:
  r=requests.get(u,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []

def bolla(nome):
 try:
  OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
  fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
  if not fx: return "Nessuna partita oggi"
  fx=sorted(fx,key=lambda x:x["fixture"]["timestamp"])
  out=[]; tot=1.0
  for p in fx:
   if len(out)>=8 or tot>=3.5: break
   dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
   if dt < datetime.now(ITALY): continue
   fid=p["fixture"]["id"]; home=p['teams']['home']['name']; away=p['teams']['away']['name']
   paese=p['league']['country']; lega=p['league']['name']
   odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
   if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
   best=None
   for b in odds[0]["bookmakers"][0]["bets"]:
    if "First" in b["name"] or "Corner" in b["name"] or "Card" in b["name"]: continue
    for v in b["values"]:
     try:
      q=float(v["odd"])
      if 1.08<=q<=1.30 and (best is None or q>best["q"]): best={"e":v["value"],"q":q,"m":b["name"]}
     except: pass
   if not best: continue
   if "Winner" in best["m"]: txt="1" if "Home" in best["e"] else "2" if "Away" in best["e"] else "X"
   else: txt=best["e"].replace("Home/Draw","1X").replace("Draw/Away","X2")
   tot*=best["q"]; qf=best["q"]*1.25
   out.append(f"🕐 {dt.strftime('%H:%M')}\n📍 {paese} - {lega}\n{home} vs {away}\n👉 {txt} + Multigol 1-5 @ {qf:.2f}")
  if not out: return f"{nome}: poche partite ora"
  return f"🔥 {nome} - Quota {tot:.2f}\n\n"+"\n\n".join(out)
 except Exception as e: return f"Errore: {e}"

def poll():
 global is_paused,last_update_id
 while True:
  try:
   url=f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25"
   r=requests.get(url,timeout=30).json()
   for up in r.get("result",[]):
    last_update_id=up["update_id"]
    txt=up.get("message",{}).get("text","").upper().strip()
    cid=up.get("message",{}).get("chat",{}).get("id")
    if not txt: continue
    if "SPEGNI" in txt: is_paused=True; tg("🛑 PAUSA",cid)
    elif "ACCENDI" in txt: is_paused=False; tg("✅ BOT ATTIVO",cid)
    elif "SCHEDINA ORA" in txt: tg("⏳ Creo...",cid); tg(bolla("SCHEDINA ORA"),cid)
    elif "PARTITE" in txt: tg("⏳ Cerco...",cid); tg(bolla("PARTITE OGGI"),cid)
    elif "BLASONATE" in txt: tg("⏳ Cerco...",cid); tg(bolla("BLASONATE"),cid)
    elif "UNDER" in txt: tg("⏳ Cerco...",cid); tg(bolla("UNDER"),cid)
    elif "TOKEN" in txt: tg(f"📊 {'PAUSA' if is_paused else 'ATTIVO'} | {datetime.now(ITALY).strftime('%H:%M')}",cid)
  except: time.sleep(5)
  time.sleep(2)
threading.Thread(target=poll,daemon=True).start()

def gs(a,n):
 for s in a:
  if s.get('type')==n:
   try: return int(str(s.get('value') or 0).replace('%','') or 0)
   except: return 0
 return 0

tg("✅ BOT V21 APPENA RIAVVIATO - Premi ACCENDI")

while True:
 try:
  if is_paused: time.sleep(30); continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10: time.sleep(300); continue
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT": time.sleep(3600); continue
  if not live: time.sleep(60); continue
  for g in live:
   fid=g["fixture"]["id"]; m=g["fixture"]["status"]["elapsed"]; st=g["fixture"]["status"]["short"]
   if m is None or fid in av_s: continue
   home=g['teams']['home']['name']; away=g['teams']['away']['name']; gh=g['goals']['home']; ga=g['goals']['away']
   paese=g['league']['country']
   def tiri():
    d=cache.get(fid)
    if not d or time.time()-d.get('time',0)>180:
     s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if s and len(s)>=2:
      sot=gs(s[0]['statistics'],'Shots on Goal')+gs(s[1]['statistics'],'Shots on Goal')
      cache[fid]={'sot':sot,'time':time.time()}; time.sleep(0.3); return sot
     return d.get('sot',0) if d else 0
    return d.get('sot',0)
   if st=="HT" and fid not in pre1:
    so=tiri()
    if so>=3: tg(f"⏸️ FINE 1T {paese} | Tiri:{so} | {home} {gh}-{ga} {away}"); pre1.add(fid)
   if 46<=m<=69 and fid not in pre:
    so=tiri()
    if so>=5: tg(f"🔔 PREPARATI {m}' {paese} | Tiri:{so} | {home} {gh}-{ga} {away}"); pre.add(fid)
   if 65<=m<=92:
    so=tiri()
    if so>=4 and fid not in av_s:
     sq=home if gh<=ga else away
     tg(f"🔥 GIOCALO {m}' {paese} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}")
     av_s.add(fid); av_g[fid]=gh+ga
  for g in live:
   fid=g["fixture"]["id"]
   if fid in av_g and g["goals"]["home"]+g["goals"]["away"]>av_g[fid]:
    tg(f"🟢 GOAL VINTO! {g['league']['country']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
    del av_g[fid]
  time.sleep(60)
 except: time.sleep(15)
