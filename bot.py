import os,time,requests,threading,json,urllib.parse
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
def home(): return "BOT V54 OK NAZIONI",200
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
  elif any(x in upper for x in ["GOL","PAREGGIA","VANTAGGIO","GOAL VINTO"]) and "🟢" not in m: m=f"🟢 {m}"
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
def get_last_10_stats(team_id):
  try:
    data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
    if not data or data=="LIMIT": return "LIMIT"
    over05=over15=over25=gg=0
    tot=len(data)
    if tot<5: return None
    for f in data:
      gh=f.get("goals",{}).get("home") or 0
      ga=f.get("goals",{}).get("away") or 0
      if gh+ga >=1: over05+=1
      if gh+ga >=2: over15+=1
      if gh+ga >=3: over25+=1
      if gh>=1 and ga>=1: gg+=1
    return {"tot":tot,"o05":over05/tot*100,"o15":over15/tot*100,"o25":over25/tot*100,"gg":gg/tot*100}
  except: return None
def get_best_stat_90(home_id,away_id):
  try:
    s1=get_last_10_stats(home_id)
    if s1=="LIMIT": return "LIMIT"
    time.sleep(0.35)
    s2=get_last_10_stats(away_id)
    if s2=="LIMIT": return "LIMIT"
    if not s1 or not s2: return None
    o05=(s1["o05"]+s2["o05"])/2; o15=(s1["o15"]+s2["o15"])/2; o25=(s1["o25"]+s2["o25"])/2; gg=(s1["gg"]+s2["gg"])/2
    best=None; best_perc=0
    if o05>=90 and o05>best_perc: best=f"Over 0.5 @ {o05:.0f}%"; best_perc=o05
    if o15>=90 and o15>best_perc: best=f"Over 1.5 @ {o15:.0f}%"; best_perc=o15
    if o25>=90 and o25>best_perc: best=f"Over 2.5 @ {o25:.0f}%"; best_perc=o25
    if gg>=90 and gg>best_perc: best=f"Gol @ {gg:.0f}%"; best_perc=gg
    return best
  except: return None
def run_bolla(cid=None,auto=False):
 try:
  tg("BOLLA MISTA 90% - Analizzo ultime 10 da adesso a mezzanotte...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  tomorrow=(datetime.now(ROME)+timedelta(days=1)).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": data=[]
  now_dt=datetime.now(ROME)
  sel=[]; checked=0
  for f in data:
   country=f.get("league",{}).get("country")
   if country not in TOP_LEAGUES: continue
   if f.get("league",{}).get("id")!=TOP_LEAGUES.get(country): continue
   if is_youth_league(f.get("league",{}).get("name","")): continue
   if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try: f_dt=datetime.fromisoformat(f.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
   except: continue
   if f
