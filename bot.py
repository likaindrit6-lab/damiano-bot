import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_id=0
av_g={}
av_s=set()
av_s_first=set()
av_sfiga_score={}

app=Flask(__name__)
@app.route("/")
def home():
 return "BOT V63 STABILE - SOLO COLORI",200

TAST=json.dumps({"keyboard":[["OVER 1.5 90%"],["STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True})

def tg(m,cid=None,keys=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys: pay["reply_markup"]=json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=15)
 except Exception as e: print(e)

def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=25)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except Exception: return []

def get_sfigata(fid):
 try:
  data=api(f"https://v3.football.api-sports.io/odds?fixture={fid}")
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:1]:
   for bet in book.get("bets",[]):
    if bet.get("name")=="Match Winner":
     q={}
     for v in bet.get("values",[]):
      try: q[v.get("value")]=float(v.get("odd"))
      except: pass
     h=q.get("Home",0); a=q.get("Away",0)
     if h>=4.5 and a<=1.8: return ("HOME",h,"AWAY",a)
     if a>=4.5 and h<=1.8: return ("AWAY",a,"HOME",h)
 except Exception: return None

def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(20); continue
   base="https://api.telegram.org/bot"+BOT
   r=requests.get(base+f"/getUpdates?offset={last_id+1}&timeout=15",timeout=25).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower()
     cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     if "accendi" in low or "/start" in low: is_paused=False; tg("BOT V63 ATTIVO - SOLO COLORI",cid,True); continue
     if "status" in low: tg("STATUS V63 OK - LIVE ATTIVI",cid,True); continue
  except: pass
  time.sleep(3)

def live_loop():
 tg("BOT V63 LIVE - COLORI ATTIVI",None,True)
 while True:
  try:
   if is_paused: time.sleep(20); continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6: time.sleep(300); continue
   games=api("https://v3.football.api-sports.io/fixtures?live=all")
   if games=="LIMIT": time.sleep(300); continue
   if not games: time.sleep(60); continue
   for g in games:
    fid=g.get("fixture",{}).get("id")
    mm=g.get("fixture",{}).get("status",{}).get("elapsed")
    if mm is None: continue
    gh=g.get("goals",{}).get("home"); ga=g.get("goals",{}).get("away")
    tm=g.get("teams",{}); home=tm.get("home",{}).get("name"); away=tm.get("away",{}).get("name")
    lg=g.get("league",{}); label=f"[{lg.get('country','')} - {lg.get('name','')}]"
    if fid not in av_sfiga_score: av_sfiga_score[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga_score[fid]
     if gh!=oh or ga!=oa:
      av_sfiga_score[fid]=(gh,ga)
      sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       chi="HOME" if gh>oh else "AWAY"
       if chi==tipo:
        sg=gh if tipo=="HOME" else ga; fg=ga if tipo=="HOME" else gh
        if sg>=fg:
         stato="PAREGGIA" if sg==fg else "VANTAGGIO"
         ns=home if tipo=="HOME" else away
         nf=away if tipo=="HOME" else home
         tg(f"⚫ SFIGATA {stato} {mm}' {label} {home} {gh}-{ga} {away}\nSfigata {ns} @{qs}\nFavorita {nf} @{qf}")
    if 30<=mm<=45 and fid not in av_s_first:
     st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if st=="LIMIT": time.sleep(80); continue
     sot=0; cor=0
     if st and len(st)>=2:
      for s in st:
       for x in s.get("statistics",[]):
        t=x.get("type","")
        if "Shots on Goal" in t:
         try: sot+=int(str(x.get("value") or 0))
         except: pass
        if "corner" in t.lower():
         try: cor+=int(str(x.get("value") or 0))
         except: pass
     if sot>=4 or cor>=6:
      tg(f"🔥 PREPARATI {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{cor}")
      av_s_first.add(fid)
    if 65<=mm<=90 and fid not in av_s:
     st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if st=="LIMIT": time.sleep(80); continue
     sot=0; cor=0
     if st and len(st)>=2:
      for s in st:
       for x in s.get("statistics",[]):
        t=x.get("type","")
        if "Shots on Goal" in t:
         try: sot+=int(str(x.get("value") or 0))
         except: pass
        if "corner" in t.lower():
         try: cor+=int(str(x.get("value") or 0))
         except: pass
     if sot>=4 or cor>=6:
      tg(f"🚀 GIOCALO {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{cor}")
      av_s.add(fid); av_g[fid]=gh+ga
   for g in games:
    fid=g.get("fixture",{}).get("id")
    if fid in av_g:
     gh2=g.get("goals",{}).get("home"); ga2=g.get("goals",{}).get("away")
     if gh2+ga2>av_g[fid]:
      lg=g.get("league",{}); label=f"[{lg.get('country','')} - {lg.get('name','')}]"
      tm=g.get("teams",{}); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
      tg(f"🟢 GOAL VINTO! {label} {hn} {gh2}-{ga2} {an}")
      del av_g[fid]
   time.sleep(90)
  except Exception as e:
   print(e); time.sleep(20)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
