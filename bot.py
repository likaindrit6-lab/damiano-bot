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
 return "BOT V54 FULL + OVER 1.5 90% + BUILDER WORLDWIDE",200
TAST=json.dumps({"keyboard":[["OVER 1.5 90% NAZIONI"],["GIALLI 85%"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["CALCIO D'ANGOLO +6"],["BAD BUILDER 1.82 WORLDWIDE"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
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
  return avg
 except:
  return None
def get_corner_avg_team(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
  if data=="LIMIT":
   return "LIMIT"
  if not data or len(data)<3:
   return None
  tot=0
  cnt=0
  for fx in data[:10]:
   fid=fx.get("fixture",{}).get("id")
   st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
   if st=="LIMIT":
    return "LIMIT"
   if not st:
    continue
   c=0
   for ts in st:
    for x in ts.get("statistics",[]):
     if "corner" in (x.get("type") or "").lower():
      try:
       c+=int(str(x.get("value") or 0))
      except:
       pass
   if c>0:
    tot+=c
    cnt+=1
   time.sleep(0.25)
  if cnt<3:
   return None
  return tot/cnt
 except:
  return None
def run_corner_over65(cid=None):
 try:
  tg("OVER 6.5 ANGOLI - PRE MATCH - STATS 10 PARTITE - Analizzo 3 min...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME)
  sel=[]
  chk=0
  for fx in data:
   lg=fx.get("league",{})
   co=lg.get("country")
   if co not in TOP:
    continue
   if is_youth(lg.get("name","")):
    continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
    continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except:
    continue
   if fdt<now_dt:
    continue
   chk+=1
   if chk>12:
    break
   tm=fx.get("teams",{})
   hid=tm.get("home",{}).get("id")
   aid=tm.get("away",{}).get("id")
   c1=get_corner_avg_team(hid)
   if c1=="LIMIT":
    time.sleep(60)
    c1=get_corner_avg_team(hid)
   if c1 is None:
    continue
   time.sleep(0.4)
   c2=get_corner_avg_team(aid)
   if c2=="LIMIT":
    time.sleep(60)
    c2=get_corner_avg_team(aid)
   if c2 is None:
    continue
   avg=(c1+c2)/2
   if avg>=6.5:
    ora=fdt.strftime("%H:%M")
    hn=tm.get("home",{}).get("name")
    an=tm.get("away",{}).get("name")
    sel.append((avg,f"{ora} [{co}] {hn} vs {an} -> Media {avg:.1f} - OVER 6.5"))
  if sel:
   sel.sort(key=lambda x: x[0], reverse=True)
   out=f"OVER 6.5 ANGOLI PRE MATCH - {len(sel)} partite OGGI (su {chk})\n\n"
   for i,(a,m) in enumerate(sel,1):
    out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else:
   tg(f"0 partite con media Over 6.5 oggi. Analizzate {chk}",cid,True)
 except Exception as e:
  tg(f"Errore Corner Over 6.5: {e}",cid,True)
def run_over90(cid=None):
 try:
  tg("OVER 1.5 90% NAZIONI - Analizzo 60 partite...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT":
   data=[]
  now_dt=datetime.now(ROME)
  sel=[]
  chk=0
  for fx in data:
   lg=fx.get("league",{})
   co=lg.get("country")
   if co not in TOP:
    continue
   if is_youth(lg.get("name","")):
    continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
    continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except:
    continue
   if fdt<now_dt:
    continue
   chk+=1
   if chk>60:
    break
   tm=fx.get("teams",{})
   hid=tm.get("home",{}).get("id")
   aid=tm.get("away",{}).get("id")
   perc=get_best90(hid,aid)
   if perc=="LIMIT":
    time.sleep(60)
    perc=get_best90(hid,aid)
   if not perc or perc<80:
    continue
   ora=fdt.strftime("%H:%M")
   hn=tm.get("home",{}).get("name")
   an=tm.get("away",{}).get("name")
   ln=lg.get("name","")
   sel.append((perc,f"{ora} [{co} - {ln}] {hn} vs {an} -> Over 1.5 @ {perc:.0f}%"))
  if sel:
   sel.sort(key=lambda x: x[0], reverse=True)
   out=f"OVER 1.5 80%+ NAZIONI - {len(sel)} partite\n\n"
   for i,(p,m) in enumerate(sel,1):
    out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else:
   tg(f"0 partite 80%+ oggi. Controllate {chk}",cid,True)
 except Exception as e:
  tg(f"Errore Over90: {e}",cid,True)
def run_gialli(cid=None):
 try:
  tg("GIALLI 85% - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME)
  sel=[]
  chk=0
  for fx in data:
   lg=fx.get("league",{})
   co=lg.get("country")
   if co not in TOP:
    continue
   if is_youth(lg.get("name","")):
    continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
    continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except:
    continue
   if fdt<now_dt:
    continue
   chk+=1
   if chk>40:
    break
   tm=fx.get("teams",{})
   hid=tm.get("home",{}).get("id")
   aid=tm.get("away",{}).get("id")
   perc=get_best90(hid,aid)
   if perc=="LIMIT":
    time.sleep(60)
    perc=get_best90(hid,aid)
   if not perc or perc<75:
    continue
   ora=fdt.strftime("%H:%M")
   hn=tm.get("home",{}).get("name")
   an=tm.get("away",{}).get("name")
   ln=lg.get("name","")
   sel.append((perc,f"{ora} [{co} - {ln}] {hn} vs {an} -> GIALLI ENTRAMBE 1+ @ {perc:.0f}%"))
  if sel:
   sel.sort(key=lambda x: x[0], reverse=True)
   out=f"GIALLI 85% - {len(sel)} partite OGGI\n\n"
   for i,(p,m) in enumerate(sel,1):
    out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else:
   tg(f"0 gialli oggi. Controllate {chk}",cid,True)
 except Exception as e:
  tg(f"Errore Gialli: {e}",cid,True)
def run_bolla(cid=None):
 try:
  tg("BOLLA EUROPA 33 NAZIONI - Creo top 5...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME)
  sel=[]
  for fx in data:
   lg=fx.get("league",{})
   co=lg.get("country")
   if co not in TOP:
    continue
   if is_youth(lg.get("name","")):
    continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
    continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except:
    continue
   if fdt<now_dt:
    continue
   tm=fx.get("teams",{})
   hid=tm.get("home",{}).get("id")
   aid=tm.get("away",{}).get("id")
   perc=get_best90(hid,aid)
   if perc=="LIMIT":
    time.sleep(60)
    perc=get_best90(hid,aid)
   if not perc or perc<82:
    continue
   ora=fdt.strftime("%H:%M")
   hn=tm.get("home",{}).get("name")
   an=tm.get("away",{}).get("name")
   ln=lg.get("name","")
   sel.append((perc,f"{ora} [{co} - {ln}] {hn} vs {an} {perc:.0f}%"))
   if len(sel)>=30:
    break
  sel.sort(key=lambda x: x[0], reverse=True)
  if sel:
   top5=sel[:5]
   out=f"BOLLA EUROPA 33 - TOP 5 ({len(sel)} trovate)\n\n"
   for i,(p,m) in enumerate(top5,1):
    out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else:
   tg("0 partite per bolla oggi",cid,True)
 except Exception as e:
  tg(f"Errore Bolla: {e}",cid,True)
def run_doppia(cid=None):
 try:
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  out=[]
  tg("Cerco DOPPIA...",cid,True)
  for fx in data:
   lg=fx.get("league",{})
   co=lg.get("country")
   if co not in TOP:
    continue
   if is_youth(lg.get("name","")):
    continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
    continue
   fid=fx.get("fixture",{}).get("id")
   odd=get_over_odd(fid)
   if odd is None or odd>1.55:
    continue
   ora=str(fx.get("fixture",{}).get("date",""))[11:16]
   tm=fx.get("teams",{})
   hn=tm.get("home",{}).get("name")
   an=tm.get("away",{}).get("name")
   ln=lg.get("name","")
   out.append(f"{ora} [{co} - {ln}] {hn} vs {an} OVER 1.5 @ {odd}")
   time.sleep(0.3)
   if len(out)>=15:
    break
  if out:
   txt="DOPPIA "+str(len(out))+" OVER 1.5\n\n"
   for i,m in enumerate(out,1):
    txt+=f"{i}. {m}\n"
   tg(txt,cid,True)
  else:
   tg("Nessuna DOPPIA oggi",cid,True)
 except Exception as e:
  tg(f"Errore doppia {e}",cid,True)
def get_builder_odds(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT":
   return None
  odds={}
  for book in data[0].get("bookmakers",[])[:4]:
   for bet in book.get("bets",[]):
    bname=bet.get("name","")
    for v in bet.get("values",[]):
     try:
      o=float(v.get("odd"))
     except:
      continue
     val=v.get("value","")
     if "Over 1.5" in val and "o15" not in odds:
      odds["o15"]=o
     if "Yes" in val and "Both Teams" in bname and "gg" not in odds:
      odds["gg"]=o
     if "Over 4.5" in val and "Corners" in bname and "o45c" not in odds:
      odds["o45c"]=o
     if "Over 6.5" in val and "Corners" in bname and "o65c" not in odds:
      odds["o65c"]=o
  return odds
 except:
  return None
def build_builder_combo(odds):
 combos=[]
 if "o15" in odds and "gg" in odds:
  tot=odds["o15"]*odds["gg"]
  if 1.65 <= tot <= 2.1:
   combos.append((tot,f"OVER 1.5 ({odds['o15']}) + GG ({odds['gg']}) = {tot:.2f}"))
 if "o15" in odds and "o45c" in odds:
  tot=odds["o15"]*odds["o45c"]
  if 1.65 <= tot <= 2.1:
   combos.append((tot,f"OVER 1.5 + OVER 4.5 Angoli = {tot:.2f}"))
 if "o65c" in odds:
  if 1.65 <= odds["o65c"] <= 2.1:
   combos.append((odds["o65c"],f"OVER 6.5 Angoli = {odds['o65c']:.2f}"))
 combos.sort(key=lambda x: abs(x[0]-1.82))
 return combos[0] if combos else None
def run_bad_builder(cid=None):
 try:
  tg("BAD BUILDER 1.82 WORLDWIDE - GIORNO E NOTTE - Cerco in TUTTO IL MONDO...",cid,True)
  now_rome=datetime.now(ROME)
  dates=[]
  for i in range(3):
   d=(now_rome+timedelta(days=i)).strftime("%Y-%m-%d")
   dates.append(d)
  sel=[]
  for date in dates:
   data=api(f"https://v3.football.api-sports.io/fixtures?date={date}") or []
   if data=="LIMIT":
    time.sleep(60)
    continue
   for fx in data:
    if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
     continue
    lg=fx.get("league",{})
    if is_y
