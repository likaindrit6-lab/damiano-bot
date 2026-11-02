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
TOP={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,"Belarus":116,"Russia":235}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b: return True
 return False
app=Flask(__name__)
@app.route("/")
def home():
 return "BOT V57 FINAL BAD BUILDER 1.82 MAX",200
TAST=json.dumps({"keyboard":[["BAD BUILDER 1.82 MAX"],["OVER 1.5 90% NAZIONI"],["DOPPIA ALTA %"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
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
 except Exception as e: print(e)
def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []
def get_all_odds_for_builder(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT" or len(data)==0: return None
  odds={}
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    name=bet.get("name","")
    for v in bet.get("values",[]):
     vn=v.get("value","")
     try: od=float(v.get("odd"))
     except: continue
     if "Over 1.5" in vn: odds["OVER15"]=od
     if "Over 0.5" in vn and "Over/Under" in name: odds["OVER05"]=od
     if "Yes" in vn and "Both Teams" in name: odds["GG"]=od
     if "Over 4.5" in vn and "Corners" in name: odds["CORN45"]=od
  return odds
 except: return None
def build_combo(odds):
 if not odds: return None
 combos=[]
 if "OVER15" in odds and "GG" in odds:
  tot=odds["OVER15"]*odds["GG"]*0.88
  if 1.70 <= tot <= 1.95:
   combos.append((tot,f"OVER 1.5 @{odds['OVER15']} + GOL @{odds['GG']}"))
 if "OVER05" in odds and "CORN45" in odds:
  tot=odds["OVER05"]*odds["CORN45"]*0.88
  if 1.70 <= tot <= 1.95:
   combos.append((tot,f"OVER 0.5 @{odds['OVER05']} + OVER 4.5 Ang @{odds['CORN45']}"))
 if combos:
  combos.sort(key=lambda x: abs(x[0]-1.82))
  return combos[0]
 return None
def run_bad_builder(cid=None):
 try:
  tg("BAD BUILDER 1.82 MAX - Cerco 8-9 partite odierne...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME)
  sel=[]; chk=0
  for fx in data:
   lg=fx.get("league",{}); co=lg.get("country")
   if co not in TOP: continue
   if lg.get("id")!=TOP.get(co): continue
   if is_youth(lg.get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except: continue
   if fdt < now_dt: continue
   chk+=1
   if chk>35: break
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("name"); aid=tm.get("away",{}).get("name")
   fid=fx.get("fixture",{}).get("id")
   odds=get_all_odds_for_builder(fid)
   if odds is None: time.sleep(0.6); continue
   combo=build_combo(odds)
   if combo:
    quota, descrizione = combo
    ora=fdt.strftime("%H:%M")
    sel.append(f"{ora} [{co}] {hid} vs {aid} -> {descrizione} -> TOT @{quota:.2f}")
   time.sleep(0.6)
   if len(sel)>=9: break
  if sel:
   out=f"BAD BUILDER 1.82 MAX - {len(sel)} partite oggi su {chk}\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n\n"
   tg(out,cid,True)
  else: tg(f"Nessun BUILDER 1.82 su {chk} partite oggi",cid,True)
 except Exception as e: tg(f"Errore Bad Builder: {e}",cid,True)
def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(20); continue
   base="https://api.telegram.org/bot"+BOT
   url=base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     if "apri menu" in low: tg("Menu aperto V57",cid,True,False); continue
     if "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     if "accendi" in low or "/start" in low: is_paused=False; tg("V57 FINAL ATTIVO + BUILDER 1.82 MAX",cid,True); continue
     if "status" in low: tg("STATUS V57 OK",cid,True); continue
     if "bad builder" in low or "builder" in low: run_bad_builder(cid); continue
  except Exception as e: print(f"poll error {e}")
  time.sleep(2)
def live_loop():
 tg("BOT V57 FINAL ATTIVO",None,True)
 while True:
  try:
   if is_paused: time.sleep(30); continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6: time.sleep(300); continue
   time.sleep(60)
  except Exception as e:
   print(f"live error {e}")
   time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
