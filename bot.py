import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
ROME=ZoneInfo("Europe/Rome")
is_paused=False
last_id=0
av_g={}
av_s=set()
av_s_first=set()
av_sfiga_score={}
TOP_LEAGUES={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,"Belarus":116,"Russia":235}
def is_youth_league(name):
    n=name.lower()
    bad=["u19","u21","u23","u17","women"," w ","female","youth","reserve","development","academy"," u18"," u20"]
    for x in bad:
        if x in n: return True
    return False
app=Flask(__name__)
@app.route("/")
def home(): return "BOT V55 OK",200
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["STATISTICHE 35 NAZIONI"],["CALCIO D'ANGOLO +6"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_CHIUSA=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False,chiusa=False,home=None,away=None):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  upper=m.upper()
  if "PREPARATI" in upper and "🔥" not in m: m=f"🔥 {m}"
  elif "GIOCALO" in upper and "🚀" not in m: m=f"🚀 {m}"
  elif any(x in upper for x in ["GOL","PAREGGIA","VANTAGGIO","GOAL VINTO","SFIGATA"]) and "🟢" not in m: m=f"🟢 {m}"
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys: pay["reply_markup"]=json.loads(TAST_CHIUSA if chiusa else TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=25)
 except Exception as e: print(e)
def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []
def get_sfigata(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid); data=api(u)
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:2]:
   for bet in book.get("bets",[]):
    if bet.get("name")=="Match Winner":
     q={}
     for v in bet.get("values",[]):
      try: q[v.get("value")]=float(v.get("odd"))
      except: pass
     h=q.get("Home",0); a=q.get("Away",0)
     if h>=4.5 and h>a and a<=1.8: return ("HOME",h,"AWAY",a)
     if a>=4.5 and a>h and h<=1.8: return ("AWAY",a,"HOME",h)
  return None
 except: return None
def get_fixtures_today():
 today=datetime.now(ROME).strftime("%Y-%m-%d")
 return api("https://v3.football.api-sports.io/fixtures?date="+today)
def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(60); continue
   base="https://api.telegram.org/bot"+BOT
   r=requests.get(base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20",timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]; msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     elif "apri menu" in low: tg("Menu aperto V55",cid,True,False); continue
     elif "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     elif "accendi" in low or "/start" in low: is_paused=False; tg("V55 ATTIVO",cid,True); continue
     elif "status" in low: tg("STATUS V55 OK",cid,True); continue
  except: pass
  time.sleep(2)
def live_loop():
 tg("BOT V55 ATTIVO",None,True)
 while True:
  try:
   if is_paused: time.sleep(30); continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6: time.sleep(300); continue
   games=api("https://v3.football.api-sports.io/fixtures?live=all")
   if games=="LIMIT": time.sleep(3600); continue
   if not games: time.sleep(60); continue
   for g in games:
    fid=g.get("fixture",{}).get("id"); mm=g.get("fixture",{}).get("status",{}).get("elapsed")
    if mm is None: continue
    home=g.get("teams",{}).get("home",{}).get("name"); away=g.get("teams",{}).get("away",{}).get("name")
    co=g.get("league",{}).get("country") or ""; lg=g.get("league",{}).get("name") or ""
    gh=g.get("goals",{}).get("home"); ga=g.get("goals",{}).get("away")
    if fid not in av_sfiga_score: av_sfiga_score[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga_score[fid]
     if gh!=oh or ga!=oa:
      chi="HOME" if gh>oh else "AWAY"; av_sfiga_score[fid]=(gh,ga)
      sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       if chi==tipo:
        sfiga_gol = gh if tipo=="HOME" else ga; fav_gol = ga if tipo=="HOME" else gh
        if sfiga_gol >= fav_gol:
            stato="PAREGGIA" if sfiga_gol==fav_gol else "VANTAGGIO"
            ns=home if tipo=="HOME" else away; nf=away if tipo=="HOME" else home
            full=f"SFIGATA {stato} {mm}' {co} - {lg}\n{home} {gh}-{ga} {away}\nSfigata {ns} @{qs}\nFavorita {nf} @{qf}"
            tg(full)
    if 30<=mm<=45 and fid not in av_s_first:
     u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid); st=api(u); sot=0; corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s.get("statistics",[]):
        if "Shots on Goal" in x.get("type",""):
         try: sot+=int(str(x.get("value") or 0))
         except: pass
        if "corner" in str(x.get("type","")).lower():
         try: corn+=int(str(x.get("value") or 0))
         except: pass
     if sot>=4 or corn>=6:
        tg(f"PREPARATI {mm}' {co} - {lg}\n{home} {gh}-{ga} {away} Tiri:{sot}"); av_s_first.add(fid)
    if 65<=mm<=90 and fid not in av_s:
     u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid); st=api(u); sot=0; corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s.get("statistics",[]):
        if "Shots on Goal" in x.get("type",""):
         try: sot+=int(str(x.get("value") or 0))
         except: pass
        if "corner" in str(x.get("type","")).lower():
         try: corn+=int(str(x.get("value") or 0))
         except: pass
     if sot>=4 or corn>=6:
        tg(f"GIOCALO {mm}' {co} - {lg}\n{home} {gh}-{ga} {away}"); av_s.add(fid); av_g[fid]=gh+ga
   for g in games:
    fid=g.get("fixture",{}).get("id")
    if fid in av_g:
     gh2=g.get("goals",{}).get("home"); ga2=g.get("goals",{}).get("away")
     if gh2+ga2>av_g[fid]:
         hn=g.get("teams",{}).get("home",{}).get("name"); an=g.get("teams",{}).get("away",{}).get("name")
         co2=g.get("league",{}).get("country"); lg2=g.get("league",{}).get("name")
         tg(f"GOAL VINTO! {co2} - {lg2}\n{hn} {gh2}-{ga2} {an}"); del av_g[fid]
   time.sleep(60)
  except Exception as e:
   print(e); time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
