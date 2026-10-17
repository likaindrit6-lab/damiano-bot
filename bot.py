import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

try:
    from zoneinfo import ZoneInfo
    ROME=ZoneInfo("Europe/Rome")
except:
    ROME=timezone(timedelta(hours=2))

app=Flask(__name__)

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
        if x in n:
            return True
    return False

@app.route("/")
def home():
    return "BOT V54 BOLLA ALTA FIX OK",200

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
  u=f"https://v3.football.api-sports.io/odds?fixture={fid}"
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
  u=f"https://v3.football.api-sports.io/odds?fixture={fid}"
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
      if "Home/Draw" in best: return f"1X @ {best_odd}"
      if "Draw/Away" in best: return f"X2 @ {best_odd}"
      if "Home/Away" in best: return f"12 @ {best_odd}"
 except: pass
 return None

def get_over_15(fid):
 try:
  u=f"https://v3.football.api-sports.io/odds?fixture={fid}"
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
 return api(f"https://v3.football.api-sports.io/fixtures?date={today}")

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=="LIMIT":
  if not auto: tg("BOLLA: Limite API",cid,True)
  return
 sel=[]
 if not auto: tg("Cerco BOLLA ALTA 90%...",cid,True)
 for country,top_id in TOP_LEAGUES.items():
  found=None
  for f in data:
   if f.get("league",{}).get("id")==top_id and f.get("league",{}).get("country")==country:
    if is_youth_league(f.get("league",{}).get("name","")): continue
    if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
    found=f; break
  if not found: continue
  fid=found.get("fixture",{}).get("id")
  dc=get_double_chance(fid)
  if dc is None: continue
  try:
   quota=float(dc.split("@")[1].strip())
   if quota>1.40: continue
  except: continue
  ora=str(found.get("fixture",{}).get("date",""))[11:16]
  home=found.get("teams",{}).get("home",{}).get("name")
  away=found.get("teams",{}).get("away",{}).get("name")
  sel.append(f"{ora} {home} vs {away} -> {dc} ALTA 90%")
  if len(sel)>=33: break
 if not sel:
  if not auto: tg("Oggi nessuna BOLLA ALTA 90%",cid,True)
  return
 out_txt=f"BOLLA ALTA 90% {len(sel)} NAZIONI - OGGI\n\n"
 n=1
 for mm in sel:
  out_txt+=f"{n}. {mm}\n"
  n+=1
 tg(out_txt,cid,True)

def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=="LIMIT": return
    out=[]
    if not auto: tg("Cerco OVER 1.5...",cid,True)
    for f in data:
        try:
            if f.get("league",{}).get("country") not in TOP_LEAGUES: continue
            if is_youth_league(f.get("league",{}).get("name","")): continue
            if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
            if f.get("league",{}).get("id")!=TOP_LEAGUES.get(f.get("league",{}).get("country")): continue
            fid=f.get("fixture",{}).get("id")
            over_odd=get_over_15(fid)
            if over_odd is None or over_odd>1.55: continue
            ora=str(f.get("fixture",{}).get("date",""))[11:16]
            home=f.get("teams",{}).get("home",{}).get("name")
            away=f.get("teams",{}).get("away",{}).get("name")
            out.append(f"{ora} {home} vs {away} OVER 1.5 @ {over_odd}")
            time.sleep(0.4)
            if len(out)>=15: break
        except: continue
    if out:
        out_txt=f"DOPPIA {len(out)} OVER 1.5\n\n"
        n=1
        for mm in out:
            out_txt+=f"{n}. {mm}\n"
            n+=1
        tg(out_txt,cid,True)
    else:
        if not auto: tg("Oggi nessun OVER 1.5",cid,True)

def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get(f"https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(60); continue
   base=f"https://api.telegram.org/bot{BOT}"
   url=f"{base}/getUpdates?offset={last_id+1}&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     elif "apri menu" in low: tg("Menu aperto V54",cid,True,False); continue
     elif "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     elif "accendi" in low or "/start" in low: is_paused=False; tg("V54 ATTIVO - BOLLA ALTA",cid,True); continue
     elif "status" in low: tg("STATUS V54 OK - BOLLA ALTA 90%",cid,True); continue
     elif "doppia" in low: run_doppia(cid); continue
     elif "bolla" in low: run_bolla(cid); continue
  except: pass
  time.sleep(2)

def live_loop():
 tg("BOT V54 ATTIVO - FIX
