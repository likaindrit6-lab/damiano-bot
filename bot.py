import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g={};av_s=set();pre=set();cache={}
token_usati=0
token_start=datetime.now(ITALY).strftime("%d/%m")
LIMITE=7500

try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home(): return "V24 FIX",200
def run_flask():
 from waitress import serve
 serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

TAST=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BLASONATE LUN-DOM","PARTITE OGGI"],["SCHEDINA ORA","TOKEN"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,cid=None,con_tastiera=True):
 try:
  p={"chat_id":str(cid or CHAT_ID),"text":m,"parse_mode":"HTML"}
  if con_tastiera: p["reply_markup"]=TAST
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json=p,timeout=20)
 except: pass

def api_get(u):
 global token_usati
 try:
  token_usati+=1
  r=requests.get(u,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []

def bolla_blasonate():
 PAESI={"Italy","England","Spain","Germany","France","Portugal","Netherlands","Belgium","Turkey","Austria","Switzerland","Denmark","Sweden","Norway","Poland","Scotland","Greece"}
 KEY=["serie a","premier league","la liga","bundesliga","ligue 1","primeira","eredivisie","jupiler","super lig"]
 OGGI=datetime.now(ITALY)
 out=[]; tot=1.0; visti=set()
 for delta in range(1,8):
  data=(OGGI+timedelta(days=delta)).strftime("%Y-%m-%d")
  fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={data}")
  if not fx or fx=="LIMIT": continue
  for p in fx:
   if len(out)>=10 or tot>=4.0: break
   if p['league']['country'] not in PAESI: continue
   lega=p['league']['name'].lower()
   if any(x in lega for x in ["u19","u21","women","amateur","cup"]): continue
   fid=p["fixture"]["id"]
   if fid in visti: continue
   odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
   if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
   best=None
   for b in odds[0]["bookmakers"][0]["bets"]:
    if "double chance" not in b["name"].lower(): continue
    for v in b["values"]:
     try:
      q=float(v["odd"])
      if not 1.10<=q<=1.30: continue
      if "Home/Draw" in v["value"]: best={"txt":"1X","q":q}
      elif "Draw/Away" in v["value"]:
       if best is None or q>best["q"]: best={"txt":"X2","q":q}
     except: pass
   if not best: continue
   visti.add(fid)
   dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
   tot*=best["q"]
   out.append(f"🕐 {dt.strftime('%a %d/%m %H:%M')}\n📍 {p['league']['country']} - {p['league']['name']}\n{p['teams']['home']['name']} vs {p['teams']['away']['name']}\n👉 {best['txt']} + Multigol 1-5 @ {best['q']*1.25:.2f}")
 return f"🔥 BLASONATE LUN-DOM EU - Quota {tot:.2f}\n\n"+"\n\n".join(out) if out else "Niente Blasonate EU fino a ven"

def bolla_oggi():
 OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
 fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
 if not fx: return "Nessuna partita"
 out=[]; tot=1.0
 for p in sorted(fx,key=lambda x:x["fixture"]["timestamp"]):
  if len(out)>=8: break
  dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
  if dt < datetime.now(ITALY): continue
  odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={p['fixture']['id']}")
  if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
  best=None
  for b in odds[0]["bookmakers"][0]["bets"]:
   if "double chance" not in b["name"].lower(): continue
   for v in b["values"]:
    try:
     q=float(v["odd"])
     if ("Home/Draw" in v["value"] or "Draw/Away" in v["value"]) and 1.08<=q<=1.30:
      txt="1X" if "Home/Draw" in v["value"] else "X2"
      if best is None or q>best["q"]: best={"txt":txt,"q":q}
    except: pass
  if not best: continue
  tot*=best["q"]
  out.append(f"🕐 {dt.strftime('%H:%M')} {p['league']['country']}\n{p['teams']['home']['name']} vs {p['teams']['away']['name']}\n👉 {best['txt']} + Multigol 1-5 @ {best['q']*1.25:.2f}")
 return f"🔥 OGGI - Quota {tot:.2f}\n\n"+"\n\n".join(out) if out else "Poche partite"

def poll():
 global is_paused,last_update_id
 while True:
  try:
   r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25",timeout=30).json()
   for up in r.get("result",[]):
    last_update_id=up["update_id"]
    txt=up.get("message",{}).get("text","").upper()
    cid=up.get("message",{}).get("chat",{}).get("id")
    if "SPEGNI" in txt: is_paused=True; tg("🛑 PAUSA",cid)
    elif "ACCENDI" in txt: is_paused=False; tg("✅ ATTIVO",cid)
    elif "BLASONATE" in txt: tg("⏳ Cerco EU...",cid); tg(bolla_blasonate(),cid)
    elif "PARTITE" in txt or "SCHEDINA" in txt: tg("⏳ Creo...",cid); tg(bolla_oggi(),cid)
    elif "TOKEN" in txt:
     rim=LIMITE-token_usati
     tg(f"💰 TOKEN\nUsati: {token_usati}\nRimanenti: {rim} / {LIMITE}\nUso: {int(token_usati/LIMITE*100)}%\nStato: {'PAUSA' if is_paused else 'ATTIVO'}",cid)
  except: time.sleep(3)
  time.sleep(2)
threading.Thread(target=poll,daemon=True).start()

def gs(a,n):
 for s in a:
  if s.get('type')==n:
   try: return int(str(s.get('value') or 0).replace('%','') or 0)
   except: return 0
 return 0

tg("✅ V24 PRONTO - BLASONATE EU + TOKEN 7500")

while True:
 try:
  if is_paused: time.sleep(30); continue
  if 0<=datetime.now(ITALY).hour<10: time.sleep(300); continue
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT": time.sleep(3600); continue
  if not live: time.sleep(60); continue
  for g in live:
   fid=g["fixture"]["id"]; m=g["fixture"]["status"]["elapsed"]
   if m is None or fid in av_s: continue
   def tiri():
    d=cache.get(fid)
    if not d or time.time()-d.get('time',0)>180:
     s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if s and len(s)>=2:
      sot=gs(s[0]['statistics'],'Shots on Goal')+gs(s[1]['statistics'],'Shots on Goal')
      cache[fid]={'sot':sot,'time':time.time()}; return sot
     return 0
    return d.get('sot',0)
   if 46<=m<=69 and fid not in pre:
    so=tiri()
    if so>=5: tg(f"🔔 {m}' {g['league']['country']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']} Tiri {so}"); pre.add(fid)
   if 65<=m<=92 and fid not in av_s:
    so=tiri()
    if so>=4:
     sq=g['teams']['home']['name'] if g['goals']['home']<=g['goals']['away'] else g['teams']['away']['name']
     tg(f"🔥 {m}' {g['league']['country']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']} NEXT {sq}")
     av_s.add(fid); av_g[fid]=g['goals']['home']+g['goals']['away']
  for g in live:
   fid=g["fixture"]["id"]
   if fid in av_g and g["goals"]["home"]+g["goals"]["away"]>av_g[fid]:
    tg(f"🟢 GOAL! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
    del av_g[fid]
  time.sleep(60)
 except: time.sleep(15)
