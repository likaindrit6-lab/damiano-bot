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
TOP={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b: return True
 return False
app=Flask(__name__)
@app.route("/")
def home(): return "BOT V55 FIX OK",200
TAST=json.dumps({"keyboard":[["OVER 1.5 90% NAZIONI"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["CALCIO D'ANGOLO +6"],["BAD BUILDER 1.82 WORLDWIDE"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_C=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys: pay["reply_markup"]=json.loads(TAST_C) if chiusa else json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except: pass
def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []
def get_sfigata(fid):
 try:
  data=api("https://v3.football.api-sports.io/odds?fixture="+str(fid))
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
 except: pass
 return None
def get_over_odd(fid):
 try:
  data=api("https://v3.football.api-sports.io/odds?fixture="+str(fid))
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    if "Over/Under" in bet.get("name",""):
     for v in bet.get("values",[]):
      if "Over 1.5" in v.get("value",""):
       try: return float(v.get("odd"))
       except: pass
 except: pass
 return None
def get_last10(team_id):
 try:
  data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
  if not data or data=="LIMIT": return "LIMIT"
  if len(data)<5: return None
  c15=0
  for f in data:
   gh=f.get("goals",{}).get("home") or 0; ga=f.get("goals",{}).get("away") or 0
   if gh+ga>=2: c15+=1
  return c15/len(data)*100
 except: return None
def get_best90(hid,aid):
 try:
  s1=get_last10(hid)
  if s1=="LIMIT": return "LIMIT"
  time.sleep(0.4)
  s2=get_last10(aid)
  if s2=="LIMIT": return "LIMIT"
  if s1 is None or s2 is None: return None
  avg=(s1+s2)/2
  return avg if avg>=90 else None
 except: return None
def get_corner_avg_team(team_id):
 try:
  data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
  if data=="LIMIT": return "LIMIT"
  if not data or len(data)<3: return None
  tot=0; cnt=0
  for fx in data[:10]:
   fid=fx.get("fixture",{}).get("id")
   st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
   if st=="LIMIT": return "LIMIT"
   if not st: continue
   c=0
   for ts in st:
    for x in ts.get("statistics",[]):
     if "corner" in (x.get("type") or "").lower():
      try: c+=int(str(x.get("value") or 0))
      except: pass
   if c>0: tot+=c; cnt+=1
   time.sleep(0.25)
  return tot/cnt if cnt>=3 else None
 except: return None
def get_team_deep_stats(team_id):
 try:
  data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
  if not data or data=="LIMIT" or len(data)<4: return None
  over15=0; gol_fatti=0; angoli=0; gialli=0; tiri=0; cnt=0
  for fx in data[:8]:
   fid=fx.get("fixture",{}).get("id")
   gh=fx.get("goals",{}).get("home") or 0; ga=fx.get("goals",{}).get("away") or 0
   is_home=fx.get("teams",{}).get("home",{}).get("id")==team_id
   gf=gh if is_home else ga
   if gh+ga>=2: over15+=1
   gol_fatti+=gf
   st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
   if st=="LIMIT": time.sleep(1); continue
   if not st: continue
   for ts in st:
    if ts.get("team",{}).get("id")!=team_id: continue
    for x in ts.get("statistics",[]):
     tp=(x.get("type") or "").lower(); val=x.get("value")
     if val is None: continue
     try: v=int(str(val))
     except: continue
     if "corner" in tp: angoli+=v
     if "yellow" in tp: gialli+=v
     if "shots on goal" in tp: tiri+=v
   cnt+=1; time.sleep(0.2)
  if cnt==0: return None
  return {"over15_pct":over15/cnt*100,"gol_avg":gol_fatti/cnt,"angoli_avg":angoli/max(1,cnt),"gialli_avg":gialli/max(1,cnt),"tiri_avg":tiri/max(1,cnt)}
 except: return None
def build_intelligent_builder(hs,aws,hn,an):
 legs=[]; quota=1.0
 if hs["gol_avg"]>=1.0 and hs["over15_pct"]>=70: legs.append(f"OVER 0.5 {hn} @1.12"); quota*=1.12
 if aws["gol_avg"]>=0.9 and aws["over15_pct"]>=70: legs.append(f"OVER 0.5 {an} @1.15"); quota*=1.15
 if hs["over15_pct"]<60 and aws["over15_pct"]<60: legs.append("UNDER 4.5 GOL @1.10"); quota*=1.10
 elif hs["over15_pct"]>=80 or aws["over15_pct"]>=80: legs.append("OVER 1.5 GOL @1.18"); quota*=1.18
 avg_ang=(hs["angoli_avg"]+aws["angoli_avg"])/2
 if avg_ang>=4.0: legs.append("OVER 6.5 ANGOLI @1.18"); quota*=1.18
 elif avg_ang>=3.0: legs.append("OVER 4.5 ANGOLI @1.12"); quota*=1.12
 if hs["gialli_avg"]>=1.8 or aws["gialli_avg"]>=1.8: legs.append("OVER 1.5 CARTELLINI @1.15"); quota*=1.15
 if hs["tiri_avg"]>=3.5: legs.append(f"OVER 0.5 TIRI {hn} @1.10"); quota*=1.10
 if len(legs)>=3 and 1.60<=quota<=1.95: return legs,quota
 if len(legs)>=4 and 1.50<=quota<=2.10: return legs,quota
 return None
def run_corner_over65(cid=None):
 try:
  tg("OVER 6.5 ANGOLI - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d"); data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME); sel=[]; chk=0
  for fx in data:
   lg=fx.get("league",{}); co=lg.get("country")
   if co not in TOP: continue
   if lg.get("id")!=TOP.get(co): continue
   if is_youth(lg.get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00"); fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   chk+=1
   if chk>12: break
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   c1=get_corner_avg_team(hid)
   if c1=="LIMIT": time.sleep(60); c1=get_corner_avg_team(hid)
   if c1 is None: continue
   time.sleep(0.4)
   c2=get_corner_avg_team(aid)
   if c2=="LIMIT": time.sleep(60); c2=get_corner_avg_team(aid)
   if c2 is None: continue
   avg=(c1+c2)/2
   if avg>=6.5:
    ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
    sel.append((avg,f"{ora} [{co}] {hn} vs {an} -> {avg:.1f}"))
  if sel:
   sel.sort(key=lambda x: x[0], reverse=True)
   out=f"OVER 6.5 ANGOLI - {len(sel)} partite\n\n"
   for i,(a,m) in enumerate(sel,1): out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else: tg(f"0 Over 6.5 oggi. Analizzate {chk}",cid,True)
 except
