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
def home(): return "BOT V54 OK",200

TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["STATISTICHE 35 NAZIONI"],["CALCIO D'ANGOLO +6"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_CHIUSA=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})

def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  upper=m.upper()
  if "PREPARATI" in upper and "🔥" not in m: m=f"🔥 {m}"
  elif "GIOCALO" in upper and "🚀" not in m: m=f"🚀 {m}"
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
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
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

def get_double_chance(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    if "Double Chance" in bet.get("name",""):
     best=None; best_odd=10
     for v in bet.get("values",[]):
      try:
       odd=float(v.get("odd"))
       if odd<best_odd: best_odd=odd; best=v.get("value")
      except: continue
     if best:
      if "Home/Draw" in best: return "1X @ "+str(best_odd)
      if "Draw/Away" in best: return "X2 @ "+str(best_odd)
      if "Home/Away" in best: return "12 @ "+str(best_odd)
 except: pass
 return None

def get_over_15(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    if "Over/Under" in bet.get("name",""):
     for v in bet.get("values",[]):
      if "Over 1.5" in v.get("value",""):
       try: return float(v.get("odd"))
       except: continue
 except: pass
 return None

def get_fixtures_today():
 today=datetime.now(ROME).strftime("%Y-%m-%d")
 return api("https://v3.football.api-sports.io/fixtures?date="+today)

def run_bolla(cid=None,auto=False):
 try:
  tg(f"BOLLA ricevuta - cerco...",cid,True)
  data=get_fixtures_today()
  if not data or data=="LIMIT":
   tg("BOLLA: Limite API o 0 partite oggi",cid,True)
   return
  sel=[]
  now_dt=datetime.now(ROME)
  now_hm=now_dt.strftime("%H:%M")
  count_check=0
  for f in data:
   try:
    if f.get("league",{}).get("country") not in TOP_LEAGUES: continue
    if f.get("league",{}).get("id")!=TOP_LEAGUES.get(f.get("league",{}).get("country")): continue
    if is_youth_league(f.get("league",{}).get("name","")): continue
    if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
    # orario reale Roma
    f_date_str=f.get("fixture",{}).get("date","")
    try:
     f_dt=datetime.fromisoformat(f_date_str.replace("Z","+00:00")).astimezone(ROME)
    except:
     f_dt=now_dt
    if f_dt < now_dt: continue
    ora=f_dt.strftime("%H:%M")
    fid=f.get("fixture",{}).get("id")
    count_check+=1
    if count_check>25: break  # per non bruciare API
    dc=get_double_chance(fid)
    if not dc: continue
    try: q=float(dc.split("@")[1].strip())
    except: continue
    if q>1.40: continue
    home=f.get("teams",{}).get("home",{}).get("name")
    away=f.get("teams",{}).get("away",{}).get("name")
    sel.append(f"{ora} {home} vs {away} -> {dc}")
    if len(sel)>=33: break
   except: continue
  if not sel:
   tg(f
