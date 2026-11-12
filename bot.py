import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo

# Supporta sia i nomi vecchi che nuovi
BOT=os.getenv("BOT_TOKEN") or os.getenv("BOT")
CHAT=os.getenv("CHAT_ID") or os.getenv("CHAT")
KEY=os.getenv("API_FOOTBALL_KEY")
BASKET_KEY=os.getenv("API_BASKETBALL_KEY") or KEY

ITALY=timezone(timedelta(hours=2))
ROME=ZoneInfo("Europe/Rome")
is_paused=False
last_id=0
av_g={}
av_s=set()
av_s_first=set()
av_sfiga={}
av_builder={}

TOP={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b: return True
 return False

app=Flask(__name__)
@app.route("/")
def home():
 return "BOT V65 CALCIO+BASKET OK",200

# TASTIERA - ho aggiunto BASKET OGGI
TAST=json.dumps({"keyboard":[["OVER 1.5 90% NAZIONI","OVER 3.5 WORLDWIDE"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["CALCIO D'ANGOLO +6"],["BAD BUILDER 1.82 WORLDWIDE","BASKET OGGI"],["STATUS"],["ACCENDI","SPEGNI"]],"resize_keyboard":True})

def tg(m,cid=None,keys=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys: pay["reply_markup"]=json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except Exception as e: print(e)

def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except Exception: return []

def api_basket(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":BASKET_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except Exception as e: print(f"basket api err {e}"); return []

def get_sfigata(fid):
 try:
  data=api(f"https://v3.football.api-sports.io/odds?fixture={fid}")
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
 except Exception: return None

def get_last10(team_id,mode):
 try:
  data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
  if not data or data=="LIMIT": return "LIMIT"
  if len(data)<5: return None
  c=0
  for f in data:
   gh=f.get("goals",{}).get("home") or 0; ga=f.get("goals",{}).get("away") or 0
   tot=gh+ga
   if mode=="15" and tot>=2: c+=1
   if mode=="35" and tot>=4: c+=1
  return c/len(data)*100
 except Exception: return None

def get_best(hid,aid,mode,limit):
 try:
  s1=get_last10(hid,mode)
  if s1=="LIMIT": return "LIMIT"
  time.sleep(0.3)
  s2=get_last10(aid,mode)
  if s2=="LIMIT": return "LIMIT"
  if s1 is None or s2 is None: return None
  avg=(s1+s2)/2
  return avg if avg>=limit else None
 except Exception: return None

def get_corner_avg(team_id):
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
   time.sleep(0.2)
  return tot/cnt if cnt>=3 else None
 except Exception: return None

def get_deep(team_id):
 try:
  data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
  if not data or data=="LIMIT" or len(data)<4: return None
  o15=0; gol=0; ang=0; gial=0; tiri=0; cnt=0
  for fx in data[:8]:
   fid=fx.get("fixture",{}).get("id")
   gh=fx.get("goals",{}).get("home") or 0; ga=fx.get("goals",{}).get("away") or 0
   is_home=fx.get("teams",{}).get("home",{}).get("id")==team_id
   gf=gh if is_home else ga
   if gh+ga>=2: o15+=1
   gol+=gf
   st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
   if st=="LIMIT": time.sleep(1); continue
   if not st: continue
   for ts in st:
    if ts.get("team",{}).get("id")!=team_id: continue
    for x in ts.get("statistics",[]):
     tp=(x.get("type") or "").lower(); v=x.get("value")
     if v is None: continue
     try: vi=int(str(v))
     except: continue
     if "corner" in tp: ang+=vi
     if "yellow" in tp: gial+=vi
     if "shots on goal" in tp: tiri+=vi
   cnt+=1; time.sleep(0.2)
  if cnt==0: return None
  return {"o15":o15/cnt*100,"gol":gol/cnt,"ang":ang/max(1,cnt),"gial":gial/max(1,cnt),"tiri":tiri/max(1,cnt)}
 except Exception: return None

def run_over90(cid=None):
 try:
  tg("OVER 1.5 90% NAZIONI - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
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
   if chk>30: break
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   perc=get_best(hid,aid,"15",90)
   if perc=="LIMIT": time.sleep(60); perc=get_best(hid,aid,"15",90)
   if not perc: continue
   ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
   sel.append(f"{ora} [{co}] {hn} vs {an} -> {perc:.0f}%")
   if len(sel)>=20: break
  if sel:
   out=f"OVER 1.5 90% - {len(sel)}\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else: tg(f"0 partite 90% su {chk}",cid,True)
 except Exception as e: tg(f"Errore Over90: {e}",cid,True)

def run_over35(cid=None):
 try:
  tg("OVER 3.5 WORLDWIDE - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": time.sleep(60); data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME); sel=[]; chk=0
  for fx in data:
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   if is_youth(fx.get("league",{}).get("name","")): continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00"); fdt=datetime.fromisoformat(fd).astimezone(ROME)
    if fdt<now_dt: continue
    ora=fdt.strftime("%H:%M")
   except: ora="oggi"
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
   co=fx.get("league",{}).get("country",""); ln=fx.get("league",{}).get("name","")
   chk+=1
   if chk>50: break
   perc=get_best(hid,aid,"35",60)
   if perc=="LIMIT": time.sleep(60); perc=get_best(hid,aid,"35",60)
   if not perc: time.sleep(0.2); continue
   sel.append((perc,f"{ora} [{co} - {ln}] {hn} vs {an} -> {perc:.0f}%"))
   if len(sel)>=15: break
   time.sleep(0.2)
  if sel:
   sel.sort(key=lambda x: x[0], reverse=True)
   out=f"OVER 3.5 WORLDWIDE - {len(sel)}\n\n"
   for i,(p,m) in enumerate(sel,1): out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else: tg(f"0 OVER 3.5 su {chk}",cid,True)
 except Exception as e: tg(f"Errore OVER 3.5: {e}",cid,True)

def run_builder(cid=None):
 try:
  global av_builder
  tg("BAD BUILDER 1.82 - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": time.sleep(60); data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  sel=[]; now_dt=datetime.now(ROME)
  for fx in data:
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   if is_youth(fx.get("league",{}).get("name","")): continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00"); fdt=datetime.fromisoformat(fd).astimezone(ROME)
    if fdt<now_dt: continue
    ora=fdt.strftime("%H:%M")
   except: ora="oggi"
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); fid=fx.get("fixture",{}).get("id")
   co=fx.get("league",{}).get("country",""); ln=fx.get("league",{}).get("name","")
   hs=get_deep(hid)
   if hs is None: time.sleep(0.5); continue
   time.sleep(0.3)
   aws=get_deep(aid)
   if aws is None: time.sleep(0.5); continue
   legs=[]; quota=1.0; checks=[]
   if hs["gol"]>=1.0 and hs["o15"]>=70:
    legs.append(f"OVER 0.5 {hn} @1.12"); quota*=1.12; checks.append(("OH",hn,True))
   if aws["gol"]>=0.9 and aws["o15"]>=70:
    legs.append(f"OVER 0.5 {an} @1.15"); quota*=1.15; checks.append(("OA",an,False))
   if hs["o15"]>=80 or aws["o15"]>=80:
    legs.append("OVER 1.5 GOL @1.18"); quota*=1.18; checks.append(("O15",None,None))
   avg_ang=(hs["ang"]+aws["ang"])/2
   if avg_ang>=4.0: legs.append("OVER 6.5 ANGOLI @1.18"); quota*=1.18; checks.append(("C65",None,None))
   elif avg_ang>=3.0: legs.append("OVER 4.5 ANGOLI @1.12"); quota*=1.12; checks.append(("C45",None,None))
   if hs["gial"]>=1.8 or aws["gial"]>=1.8:
    legs.append("OVER 1.5 GIALLE @1.15"); quota*=1.15; checks.append(("G15",None,None))
   if len(legs)>=3 and 1.6<=quota<=1.95:
    desc="\n".join([f"   + {l}" for l in legs])
    sel.append(f"{ora} [{co} - {ln}] {hn} vs {an}\n{desc}\n   = @{quota:.2f}")
    av_builder[fid]={"label":f"[{co} - {ln}] {hn} vs {an}","legs":legs,"checks":checks,"quota":quota}
   time.sleep(0.3)
   if len(sel)>=10: break
  if sel:
   out=f"BAD BUILDER 1.82 - {len(sel)} OGGI {today}\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n\n"
   out+="Ti avviso io VINTO/PERSO!"
   tg(out,cid,True)
  else: tg(f"0 builder per OGGI {today}",cid,True)
 except Exception as e: tg(f"Errore Builder: {e}",cid,True)

# ============ NUOVO BASKET ============
def run_basket(cid=None):
 try:
  tg("🏀 NBA OGGI - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  # NBA = league 12 su API-BASKETBALL
  data=api_basket(f"https://v1.basketball.api-sports.io/games?date={today}&league=12") or []
  if data=="LIMIT":
   time.sleep(60)
   data=api_basket(f"https://v1.basketball.api-sports.io/games?date={today}&league=12") or []
  
  if not data:
   tg(f"🏀 NBA - Nessuna partita oggi {today}\nNBA è in pausa o date senza gare.",cid,True)
   return

  out=f"🏀 <b>NBA OGGI {today} - {len(data)} partite</b>\n\n"
  for i,g in enumerate(data,1):
   tm=g.get("teams",{})
   home=tm.get("home",{}).get("name","?")
   away=tm.get("away",{}).get("name","?")
   try:
    fd=g.get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
    ora=fdt.strftime("%H:%M")
   except:
    ora=g.get("time","")
   status=g.get("status",{}).get("long","")
   out+=f"{i}. {ora} - {away} @ {home} ({status})\n"
  
  out+="\n<i>Report giornaliero automatico 08:00</i>"
  tg(out,cid,True)
 except Exception as e:
  tg(f"Errore BASKET: {e}",cid,True)

def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(20); continue
   base="https://api.telegram.org/bot"+BOT
   url=base+f"/getUpdates?offset={last_id+1}&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]; msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     if "accendi" in low or "/start" in low: is_paused=False; tg("V65 CALCIO+BASKET OK",cid,True); continue
     if "status" in low: tg(f"V65 OK - BUILDER {len(av_builder)}",cid,True); continue
     if "over 1.5" in low and "90" in low: run_over90(cid); continue
     if "over 3.5" in low: run_over35(cid); continue
     if "builder" in low: run_builder(cid); continue
     if "basket" in low or "nba" in low: run_basket(cid); continue
  except: pass
  time.sleep(2)

def live_loop():
 tg("BOT V65 LIVE - CALCIO + BASKET 08:00",None,True)
 while True:
  try:
   if is_paused: time.sleep(30); continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6: time.sleep(300); continue
   games=api("https://v3.football.api-sports.io/fixtures?live=all")
   if games=="LIMIT": time.sleep(300); continue
   if not games: time.sleep(60); continue
   for g in games:
    fid=g.get("fixture",{}).get("id"); mm=g.get("fixture",{}).get("status",{}).get("elapsed")
    if mm is None: continue
    gh=g.get("goals",{}).get("home"); ga=g.get("goals",{}).get("away")
    tm=g.get("teams",{}); home=tm.get("home",{}).get("name"); away=tm.get("away",{}).get("name")
    lg=g.get("league",{}); label=f"[{lg.get('country','')} - {lg.get('name','')}]"
    if fid not in av_sfiga: av_sfiga[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga[fid]
     if gh!=oh or ga!=oa:
      av_sfiga[fid]=(gh,ga)
      sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       chi="HOME" if gh>oh else "AWAY"
       if chi==tipo:
        sg=gh if tipo=="HOME" else ga; fg=ga if tipo=="HOME" else gh
        if sg>=fg:
         stato="PAREGGIA" if sg==fg else "VANTAGGIO"
         ns=home if tipo=="HOME" else away
         tg(f"⚫ SFIGATA {stato} {mm}' {label} {home} {gh}-{ga} {away} Sfigata {ns} @{qs}")
    if 30<=mm<=45 and fid not in av_s_first:
     st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if st=="LIMIT": time.sleep(70); continue
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
      tg(f"🔥 PREPARATI {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{cor}"); av_s_first.add(fid)
    if 65<=mm<=90 and fid not in av_s:
     st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if st=="LIMIT": time.sleep(70); continue
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
      tg(f"🚀 GIOCALO {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{cor}"); av_s.add(fid); av_g[fid]=gh+ga
   for g in games:
    fid=g.get("fixture",{}).get("id")
    if fid in av_g:
     gh2=g.get("goals",{}).get("home"); ga2=g.get("goals",{}).get("away")
     if gh2+ga2>av_g[fid]:
      lg=g.get("league",{}); label=f"[{lg.get('country','')} - {lg.get('name','')}]"; tm=g.get("teams",{}); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
      tg(f"🟢 GOAL VINTO! {label} {hn} {gh2}-{ga2} {an}"); del av_g[fid]
   time.sleep(90)
  except Exception as e: print(e); time.sleep(20)

def builder_tracker():
 while True:
  try:
   time.sleep(600)
   if not av_builder: continue
   if is_paused: continue
   for fid in list(av_builder.keys()):
    gdata=api(f"https://v3.football.api-sports.io/fixtures?id={fid}")
    if gdata=="LIMIT": time.sleep(70); continue
    if not gdata: continue
    g=gdata[0]
    if g.get("fixture",{}).get("status",{}).get("short") not in ["FT","AET","PEN"]: continue
    gh=g.get("goals",{}).get("home") or 0; ga=g.get("goals",{}).get("away") or 0
    info=av_builder[fid]
    st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
    if st=="LIMIT": time.sleep(70); continue
    corners=0
    if st:
     for ts in st:
      for x in ts.get("statistics",[]):
       if "corner" in (x.get("type") or "").lower():
        try: corners+=int(str(x.get("value") or 0))
        except: pass
    vinto=True; mot=""
    for ctype,cteam,ih in info["checks"]:
     if ctype=="OH" and gh==0: vinto=False; mot=f"mancava {cteam}"
     if ctype=="OA" and ga==0: vinto=False; mot=f"mancava {cteam}"
     if ctype=="O15" and gh+ga<2: vinto=False; mot=f"OVER 1.5 {gh+ga}"
     if ctype=="C65" and corners<7: vinto=False; mot=f"angoli {corners}"
     if ctype=="C45" and corners<5: vinto=False; mot=f"angoli {corners}"
     if not vinto: break
    if vinto: tg(f"🟢 BUILDER VINTO! {info['label']} {gh}-{ga} Ang:{corners} @{info['quota']:.2f}")
    else: tg(f"🔴 BUILDER PERSO! {info['label']} {gh}-{ga} Ang:{corners} @{info['quota']:.2f} Motivo:{mot}")
    del av_builder[fid]; time.sleep(2)
  except Exception as e: print(f"tracker err {e}"); time.sleep(30)

def basket_scheduler():
 last_sent=None
 while True:
  try:
   now=datetime.now(ROME)
   if now.hour==8 and now.minute==0 and now.date()!=last_sent:
   
