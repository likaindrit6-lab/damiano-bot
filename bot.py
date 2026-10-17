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
  up=m.upper()
  if "PREPARATI" in up and "🔥" not in m: m=f"🔥 {m}"
  elif "GIOCALO" in up and "🚀" not in m: m=f"🚀 {m}"
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys: pay["reply_markup"]=json.loads(TAST_CHIUSA if chiusa else TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=25)
 except: print("tg error")

def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []

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

def get_fixtures_today():
 today=datetime.now(ROME).strftime("%Y-%m-%d")
 return api(f"https://v3.football.api-sports.io/fixtures?date={today}")

def run_bolla(cid=None,auto=False):
 try:
  tg("BOLLA ricevuta - cerco dalle adesso a mezzanotte...",cid,True)
  data=get_fixtures_today()
  if data=="LIMIT" or not data:
   tg("BOLLA: Limite API",cid,True)
   return
  sel=[]
  now_dt=datetime.now(ROME)
  cnt=0
  for f in data:
   if f.get("league",{}).get("country") not in TOP_LEAGUES: continue
   if f.get("league",{}).get("id")!=TOP_LEAGUES.get(f.get("league",{}).get("country")): continue
   if is_youth_league(f.get("league",{}).get("name","")): continue
   if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try:
    f_dt=datetime.fromisoformat(f.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
   except: continue
   if f_dt < now_dt: continue
   fid=f.get("fixture",{}).get("id")
   cnt+=1
   if cnt>30: break
   dc=get_double_chance(fid)
   if not dc: continue
   try: q=float(dc.split("@")[1].strip())
   except: continue
   if q>1.40: continue
   sel.append(f"{f_dt.strftime('%H:%M')} {f.get('teams',{}).get('home',{}).get('name')} vs {f.get('teams',{}).get('away',{}).get('name')} -> {dc}")
   if len(sel)>=33: break
  if not sel:
   tg(f"0 BOLLA ALTA <=1.40 dalle {now_dt.strftime('%H:%M')} a mezzanotte",cid,True)
   return
  out=f"BOLLA ALTA 90% - {len(sel)} partite fino a mezzanotte\n\n"
  for i,m in enumerate(sel,1): out+=f"{i}. {m}\n"
  tg(out,cid,True)
 except Exception as e:
  tg(f"Errore bolla: {e}",cid,True)

def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get(f"https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(60); continue
   base=f"https://api.telegram.org/bot{BOT}"
   url=base+f"/getUpdates?offset={last_id+1}&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     elif "apri menu" in low: tg("Menu aperto V54",cid,True,False); continue
     elif "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     elif "accendi" in low or "/start" in low: is_paused=False; tg("V54 ATTIVO",cid,True); continue
     elif "status" in low: tg("STATUS V54 OK",cid,True); continue
     elif "bolla" in low:
      threading.Thread(target=run_bolla,args=(cid,False),daemon=True).start()
      continue
  except: pass
  time.sleep(2)

def live_loop():
 tg("BOT V54 ATTIVO",None,True)
 while True:
  time.sleep(60)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
