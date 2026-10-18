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
TOP={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,"Belarus":116,"Russia":235}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b: return True
 return False
app=Flask(__name__)
@app.route("/")
def home(): return "BOT V55 FULL OK",200
TAST=json.dumps({"keyboard":[["OVER 1.5 90% NAZIONI"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["CALCIO D'ANGOLO +6"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_C=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys:
   pay["reply_markup"]=json.loads(TAST_C) if chiusa else json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except: pass
def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []
def get_last10(tid):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={tid}&last=10&status=FT"
  d=api(u)
  if not d or d=="LIMIT": return d
  if len(d)<5: return None
  c=0
  for f in d:
   gh=f.get("goals",{}).get("home") or 0
   ga=f.get("goals",{}).get("away") or 0
   if gh+ga>=2: c+=1
  return c/len(d)*100
 except: return None
def get_avg(hid,aid):
 try:
  s1=get_last10(hid)
  if s1=="LIMIT": return "LIMIT"
  time.sleep(0.35)
  s2=get_last10(aid)
  if s2=="LIMIT": return "LIMIT"
  if s1 is None or s2 is None: return None
  return (s1+s2)/2
 except: return None

def run_over90(cid=None):
 try:
  tg("OVER 1.5 90% - Analizzo da ora a mezzanotte...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": data=[]
  now_dt=datetime.now(ROME)
  sel=[]; chk=0
  for fx in data:
   lg=fx.get("league",{}); co=lg.get("country")
   if co not in TOP or lg.get("id")!=TOP.get(co): continue
   if is_youth(lg.get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   chk+=1
   if chk>25: break
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   perc=get_avg(hid,aid)
   if perc=="LIMIT": time.sleep(60); perc=get_avg(hid,aid)
   if not perc or perc<90: continue
   ora=fdt.strftime("%H:%M")
   sel.append(f"{ora} [{co}] {tm.get('home',{}).get('name')} vs {tm.get('away',{}).get('name')} -> {perc:.0f}%")
   if len(sel)>=15: break
  if sel:
   out=f"OVER 1.5 90% NAZIONI - {len(sel)} partite\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else: tg(f"0 partite 90% oggi. Controllate {chk}",cid,True)
 except Exception as e: tg(f"Errore Over90: {e}",cid,True)

def run_bolla(cid=None):
 try:
  tg("BOLLA EUROPA - Cerco 5 partite migliori Over 1.5 80%+...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": data=[]
  now_dt=datetime.now(ROME)
  cand=[]; chk=0
  for fx in data:
   lg=fx.get("league",{}); co=lg.get("country")
   if co not in TOP or lg.get("id")!=TOP.get(co): continue
   if is_youth(lg.get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   chk+=1
   if chk>30: break
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   perc=get_avg(hid,aid)
   if perc=="LIMIT": time.sleep(60); perc=get_avg(hid,aid)
   if not perc or perc<80: continue
   ora=fdt.strftime("%H:%M")
   cand.append((perc,f"{ora} [{co} - {lg.get('name')}] {tm.get('home',{}).get('name')} vs {tm.get('away',{}).get('name')} -> Over 1.5 {perc:.0f}%"))
  cand.sort(reverse=True)
  if cand:
   best=cand[:5]
   out=f"BOLLA EUROPA 33 NAZIONI - 5 partite TOP (da {chk} analizzate)\n\n"
   for i,(p,m) in enumerate(best,1): out+=f"{i}. {m}\n"
   out+="\nGioca singole o bolla a sistema."
   tg(out,cid,True)
  else: tg(f"0 partite per bolla 80% oggi. Analizzate {chk}",cid,True)
 except Exception as e: tg(f"Errore Bolla: {e}",cid,True)

def run_corner(cid=None):
 try:
  tg("CALCIO D'ANGOLO +6 - Controllo LIVE...",cid,True)
  games=api("https://v3.football.api-sports.io/fixtures?live=all") or []
  if games=="LIMIT": tg("API al limite, riprova tra 1h",cid,True); return
  found=[]
  for g in games:
   fid=g.get("fixture",{}).get("id"); mm=g.get("fixture",{}).get("status",{}).get("elapsed")
   if mm is None or mm<10: continue
   lg=g.get("league",{}); co=lg.get("country")
   if co not in TOP: continue
   # corner stats
   cor=0; sot=0
   st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
   if st and st!="LIMIT":
    for ts in st:
     for x in ts.get("statistics",[]):
      t=(x.get("type") or "").lower(); v=x.get("value")
      if v is None: continue
      try: val=int(str(v))
      except: continue
      if "corner" in t: cor+=val
      if "shots on goal" in t or "on target" in t: sot+=val
   if cor==0:
    ev=api(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}")
    if ev and ev!="LIMIT":
     for e in ev:
      if (e.get("type") or "").lower()=="corner": cor+=1
   if cor>=6:
    tm=g.get("teams",{}); gh=g.get("goals",{}).get("home"); ga=g.get("goals",{}).get("away")
    found.append(f"{mm}' [{co}] {tm.get('home',{}).get('name')} {gh}-{ga} {tm.get('away',{}).get('name')} Corner:{cor} Tiri:{sot}")
   time.sleep(0.2)
  if found:
   out=f"ANGOLI +6 LIVE - {len(found)} partite\n\n"
   for f in found[:15]: out+=f"- {f}\n"
   tg(out,cid,True)
  else:
   tg(f"0 partite LIVE con +6 corner al momento. Controllate {len(games)} live.",cid,True)
 except Exception as e: tg(f"Errore Corner: {e}",cid,True)

def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(20); continue
   base="https://api.telegram.org/bot"+BOT
   r=requests.get(base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20",timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]; msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     if "apri menu" in low: tg("Menu aperto V55",cid,True,False); continue
     if "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     if "accendi" in low or "/start" in low: is_paused=False; tg("V55 FULL ATTIVO",cid,True); continue
     if "status" in low: tg("STATUS V55 FULL OK - Over90 + Bolla + Corner",cid,True); continue
     if "over 1.5" in low and "90" in low: run_over90(cid); continue
     if "bolla" in low: run_bolla(cid); continue
     if "doppia" in low: tg("DOPPIA momentaneamente usa BOLLA - sono simili",cid,True); continue
     if "angolo" in low or "calcio d'angolo" in low: run_corner(cid); continue
  except: pass
  time.sleep(2)

def live_loop():
 tg("BOT V55 FULL ATTIVO - Bolla + Over90 + Corner +6",None,True)
 while True:
  try:
   if is_paused: time.sleep(30); continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6: time.sleep(300); continue
   games=api("https://v3.football.api-sports.io/fixtures?live=all")
   if games=="LIMIT": time.sleep(3600); continue
   if not games: time.sleep(60); continue
   time.sleep(60)
  except: time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
