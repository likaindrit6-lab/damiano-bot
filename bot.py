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
TOP={
"Italy":135,"England":39,"Spain":140,"Germany":78,
"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,
"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,
"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,
"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,
"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,
"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,
"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,
"Belarus":116,"Russia":235
}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b:
   return True
 return False
app=Flask(__name__)
@app.route("/")
def home():
 return "BOT V54 FULL + BUILDER WORLDWIDE",200
TAST=json.dumps({"keyboard":[["BAD BUILDER 1.82 WORLDWIDE"],["OVER 1.5 90% NAZIONI"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["CALCIO D'ANGOLO +6"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_C=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT:
   return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys:
   if chiusa:
    pay["reply_markup"]=json.loads(TAST_C)
   else:
    pay["reply_markup"]=json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except Exception as e:
  print(e)
def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429:
   return "LIMIT"
  return r.json().get("response",[])
 except:
  return []

# === FUNZIONI NUOVE BUILDER WORLDWIDE ===
def get_builder_odds(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT" or len(data)==0:
   return {}
  odds={}
  for book in data[0].get("bookmakers",[])[:4]:
   for bet in book.get("bets",[]):
    bname=bet.get("name","")
    for v in bet.get("values",[]):
     vn=v.get("value","")
     try: od=float(v.get("odd"))
     except: continue
     if "Over 1.5" in vn: odds["OVER15"]=od
     if "Over 0.5" in vn and "Over/Under" in bname: odds["OVER05"]=od
     if "Yes" in vn and "Both Teams" in bname: odds["GG"]=od
     if "Over 4.5" in vn and "Corners" in bname: odds["CORN45"]=od
     if "Over 6.5" in vn and "Corners" in bname: odds["CORN65"]=od
  return odds
 except:
  return {}

def build_builder_combo(odds):
 if not odds: return None
 combos=[]
 if "OVER15" in odds and "GG" in odds:
  tot=odds["OVER15"]*odds["GG"]*0.88
  if 1.70 <= tot <= 1.95:
   combos.append((tot,f"OVER 1.5 @{odds['OVER15']} + GOL @{odds['GG']}"))
 if "OVER05" in odds and "CORN45" in odds:
  tot=odds["OVER05"]*odds["CORN45"]*0.88
  if 1.70 <= tot <= 1.95:
   combos.append((tot,f"OVER 0.5 @{odds['OVER05']} + OVER 4.5 Angoli @{odds['CORN45']}"))
 if "CORN65" in odds:
  if 1.70 <= odds["CORN65"] <= 1.95:
   combos.append((odds["CORN65"],f"OVER 6.5 Angoli @{odds['CORN65']}"))
 if combos:
  combos.sort(key=lambda x: abs(x[0]-1.82))
  return combos[0]
 return None

def run_bad_builder(cid=None):
 try:
  tg("BAD BUILDER 1.82 WORLDWIDE - Cerco tutto il mondo oggi... 200 partite",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if not data:
   tg("API vuota per oggi",cid,True)
   return
  tg(f"Trovate {len(data)} partite nel mondo oggi - analizzo...",cid,True)
  sel=[]
  chk=0
  for fx in data:
   if is_youth(fx.get("league",{}).get("name","")):
    continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
    continue
   chk+=1
   if chk>150:
    break
   co=fx.get("league",{}).get("country","")
   lg=fx.get("league",{}).get("name","")
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
    ora=fdt.strftime("%H:%M")
   except:
    ora="??:??"
   tm=fx.get("teams",{})
   hn=tm.get("home",{}).get("name")
   an=tm.get("away",{}).get("name")
   fid=fx.get("fixture",{}).get("id")
   odds=get_builder_odds(fid)
   combo=build_builder_combo(odds)
   if combo:
    q,d=combo
    sel.append(f"{ora} [{co} {lg}] {hn} vs {an} -> {d} -> TOT @{q:.2f}")
   time.sleep(0.35)
   if len(sel)>=9:
    break
  if sel:
   out=f"BAD BUILDER 1.82 WORLDWIDE - {len(sel)} partite OGGI su {len(data)} totali (controllate {chk})\n\n"
   for i,m in enumerate(sel,1):
    out+=f"{i}. {m}\n\n"
   tg(out,cid,True)
  else:
   tg(f"Nessun BUILDER 1.82 trovato su {chk} partite controllate oggi. API manda poche quote a quest'ora, riprova tra 2-3 ore o domattina",cid,True)
 except Exception as e:
  tg(f"Errore Builder: {e}",cid,True)
# === FINE FUNZIONI NUOVE ===

def get_sfigata(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT":
   return None
  for book in data[0].get("bookmakers",[])[:2]:
   for bet in book.get("bets",[]):
    if bet.get("name")=="Match Winner":
     q={}
     for v in bet.get("values",[]):
      try:
       q[v.get("value")]=float(v.get("odd"))
      except:
       pass
     h=q.get("Home",0)
     a=q.get("Away",0)
     if h>=4.5 and h>a and a<=1.8:
      return ("HOME",h,"AWAY",a)
     if a>=4.5 and a>h and h<=1.8:
      return ("AWAY",a,"HOME",h)
  return None
 except:
  return None
def get_over_odd(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT":
   return None
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    if "Over/Under" in bet.get("name",""):
     for v in bet.get("values",[]):
      if "Over 1.5" in v.get("value",""):
       try:
        return float(v.get("odd"))
       except:
        pass
 except:
  pass
 return None
def get_last10(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
  if not data or data=="LIMIT":
   return "LIMIT"
  tot=len(data)
  if tot<5:
   return None
  c15=0
  for f in data:
   gh=f.get("goals",{}).get("home") or 0
   ga=f.get("goals",{}).get("away") or 0
   if gh+ga>=2:
    c15+=1
  return c15/tot*100
 except:
  return None
def get_best90(hid,aid):
 try:
  s1=get_last10(hid)
  if s1=="LIMIT":
   return "LIMIT"
  time.sleep(0.4)
  s2=get_last10(aid)
  if s2=="LIMIT":
   return "LIMIT"
  if s1 is None or s2 is None:
   return None
  avg=(s1+s2)/2
  if avg>=
