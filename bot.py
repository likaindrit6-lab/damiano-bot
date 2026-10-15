import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False;last_update_id=0;av_g={};av_s=set();pre=set();pre1=set();cache={}

TOP33={"Italia":135,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,"Portogallo":94,"Olanda":88,"Belgio":144,"Turchia":203,"Scozia":179,"Austria":218,"Svizzera":207,"Danimarca":119,"Svezia":113,"Norvegia":103,"Polonia":106,"Rep Ceca":110,"Croazia":210,"Serbia":286,"Grecia":197}
ALLOWED=set(list(TOP33.values())+[136,40,140,78,61,88,94,144,203])

try:requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except:pass

app=Flask(__name__)
@app.route('/')
def home():return "V74 LIVE WORLD + BOLLA EU - OK",200
threading.Thread(target=lambda: app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()

TASTIERA_JSON=json.dumps({"keyboard":[
["🟢 ACCENDI","🔴 SPEGNI"],
["Serie A","Serie B","Inghilterra"],
["Spagna","Germania","Francia"],
["LIVE","RIPARTITE"],
["PRIMO TEMPO","PREPARATI E SEGNA"],
["DOPPIA 90%","BOLLA EUROPA 33 NAZIONI"],
["🎫 BOLLA","📊 STATUS"],
["❌ CHIUDI MENU"]
],"resize_keyboard":True,"is_persistent":False})
TASTIERA_CHIUSA=json.dumps({"keyboard":[["🎮 APRI MENU"]],"resize_keyboard":True,"is_persistent":False})

def tg(m,cid=None,k=False,chiusa=False):
 try:
  cid=cid or CHAT_ID
  url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if k: pay["reply_markup"]=json.loads(TASTIERA_CHIUSA if chiusa else TASTIERA_JSON)
  requests.post(url,json=pay,timeout=25)
 except:pass

def api_get(u):
 try:
  r=requests.get(u,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429:return "LIMIT"
  return r.json().get("response",[])
 except:return []

def get_stat(a,n):
 for s in a:
  if s.get('type')==n:
   try:return int(str(s.get('value') or 0).replace('%','') or 0)
   except:return 0
 return 0
def get_flag(p):return {"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷"}.get(p,f"[{p}]")

def crea_bolla():
 try:
  OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
  fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
  fixtures=[g for g in fixtures if g['league']['id'] in ALLOWED] # SOLO EUROPA
  if not fixtures:return "Nessuna partita Europa oggi"
  picks=[];quota_tot=1.0
  for p in sorted(fixtures,key=lambda x:x["fixture"]["timestamp"]):
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
      if 1.08<=q<=1.30 and (best is None or q>best["q"]):best={"e":v["value"],"q":q}
     except:continue
   if not best or quota_tot*best["q"]>3.45:continue
   quota_tot*=best["q"];picks.append(f"🕐 {orario} 📍 {paese} - {lega}\n{home} vs {away}\n👉 {best['e']} + Multigol 1-5 @ {best['q']*1.25:.2f}")
  return f"🔥 BOLLA EUROPA 33 - Quota {quota_tot:.2f}\n\n"+"\n\n".join(picks) if len(picks)>=5 else f"Poche partite Europa: {len(picks)}"
 except Exception as e:return f"Errore: {e}"

def poll_commands():
 global is_paused,last_update_id
 while True:
  try:
   r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25",timeout=35).json()
   if r.get("ok"):
    for upd in r.get("result",[]):
     last_update_id=upd["update_id"];txt=(upd.get("message",{}).get("text") or "").strip();low=txt.lower();cid=upd.get("message",{}).get("chat",{}).get("id")
     if "chiudi menu" in low:tg("✅ Menu chiuso - Clicca 🎮 APRI MENU",cid,True,True);continue
     elif "apri menu" in low:tg("✅ Menu aperto - LIVE = MONDO, BOLLA = EUROPA",cid,True,False);continue
     elif "spegni" in low:is_paused=True;tg("🛑 PAUSA",cid,True)
     elif "accendi" in low or low=="/start":is_paused=False;tg("✅ BOT RIPRESO\n🌍 LIVE = TUTTO IL MONDO\n🇪🇺 BOLLA = SOLO EUROPA 33",cid,True)
     elif "status" in low:tg(f"📊 ATTIVO {datetime.now(ITALY).strftime('%H:%M')}\n🌍 LIVE: WORLD\n🇪🇺 BOLLA: EUROPA 33",cid,True)
     elif "bolla europa" in low or "bolla" in low or "doppia" in low:tg("⏳ Creo bolla SOLO EUROPA...",cid);tg(crea_bolla(),cid,True)
  except:pass
  time.sleep(2)
threading.Thread(target=poll_commands,daemon=True).start()

# LOOP LIVE = TUTTO IL MONDO - NON FILTRO
while True:
 try:
  if is_paused:time.sleep(30);continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear()
   time.sleep(300);continue
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT" or not live:time.sleep(60);continue
  # NON FILTRO - LIVE MONDO
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
      cache[fid]={'sot':sot,'corn':corn,'time':time.time()};time.sleep(0.3);return sot,corn
     return d.get('sot',0),d.get('corn',0) if d else (0,0)
    return d.get('sot',0),d.get('corn',0)
   if st=="HT" and fid not in pre1:
    so,co=stats_live()
    if so>=3:tg(f"⏸️ FINE 1T {pref} | Tiri:{so} Corner:{co} | {home} {gh}-{ga} {away}");pre1.add(fid)
   if 46<=(m or 0)<=69 and fid not in pre:
    so,co=stats_live()
    if so>=5 or co>=6:tg(f"🔔 PREPARATI {m}' {pref} | Tiri:{so} Corner:{co} | {home} {gh}-{ga} {away}");pre.add(fid)
   if 65<=(m or 0)<=92:
    so,co=stats_live()
    if (so>=4 or co>=7) and fid not in av_s:
     sq=home if gh<=ga else away;tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} Corner:{co} | {home} {gh}-{ga} {away} | NEXT {sq}");av_s.add(fid);av_g[fid]=gh+ga
  time.sleep(45)
 except:time.sleep(15)
