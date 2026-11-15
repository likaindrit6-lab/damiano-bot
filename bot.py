import os,time,requests,threading,json
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
ROME=ZoneInfo("Europe/Rome")
is_paused=False
last_id=0
av_g={}
av_s_first=set()
av_live7=set()
av_sfiga_score={}
av_sfiga_sent=set()
seen=set()
TOP={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,"Belarus":116,"Russia":235}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b: return True
 return False
TAST=json.dumps({"keyboard":[["OVER 1.5 90% NAZIONI"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["GIALLI 65%"],["CALCIO D'ANGOLO +6"],["BAD BUILDER 1.82 WORLDWIDE"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_C=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
sent_cache={}
def tg(m,cid=None,keys=False,chiusa=False,inline_btn=None):
 try:
  h=hash(m[:100]); now=time.time()
  if h in sent_cache and now-sent_cache[h]<30: return
  sent_cache[h]=now
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if inline_btn: pay["reply_markup"]=inline_btn
  elif keys:
   if chiusa: pay["reply_markup"]=json.loads(TAST_C)
   else: pay["reply_markup"]=json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except Exception as e: print(e)
def make_bet365_btn(home,away):
  q=quote_plus(f"{home} {away}")
  url=f"https://www.bet365.com/search?q={q}"
  return {"inline_keyboard": [[{"text": f"🎯 BET365 - {home} vs {away}", "url": url}]]}
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
def get_over_odd(fid):
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
       except: pass
 except: pass
 return None
def get_live_quote_160_170(fid):
 try:
  u=f"https://v3.football.api-sports.io/odds/live?fixture={fid}"
  data=api(u)
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    for v in bet.get("values",[]):
     try:
      odd=float(v.get("odd"))
      if 1.60 <= odd <= 1.75:
       if "Over" in v.get("value","") or "Goal" in bet.get("name",""): return odd
     except: continue
  return None
 except: return None
def get_last10(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
  if not data or data=="LIMIT": return "LIMIT"
  tot=len(data)
  if tot<5: return None
  c15=0
  for f in data:
   gh=f.get("goals",{}).get("home") or 0; ga=f.get("goals",{}).get("away") or 0
   if gh+ga>=2: c15+=1
  return c15/tot*100
 except: return None
def get_best90(hid,aid):
 try:
  s1=get_last10(hid)
  if s1=="LIMIT": return "LIMIT"
  time.sleep(0.4)
  s2=get_last10(aid)
  if s2=="LIMIT": return "LIMIT"
  if s1 is None or s2 is None: return None
  if s1>=80 and s2>=80: return (s1+s2)/2
  return None
 except: return None
def get_corner_avg_team(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
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
  if cnt<3: return None
  return tot/cnt
 except: return None
def run_corner_over65(cid=None):
 try:
  tg("OVER 6.5 ANGOLI - PRE MATCH - STATS 10 PARTITE - Analizzo 3 min...",cid,True)
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
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
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
    sel.append((avg,f"{ora} [{co}] {hn} vs {an} -> Media {avg:.1f} - OVER 6.5"))
  if sel:
   sel.sort(key=lambda x: x[0], reverse=True)
   out=f"OVER 6.5 ANGOLI PRE MATCH - {len(sel)} partite OGGI (su {chk})\n\n"
   for i,(a,m) in enumerate(sel,1): out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else: tg(f"0 partite con media Over 6.5 oggi. Analizzate {chk}",cid,True)
 except Exception as e: tg(f"Errore Corner Over 6.5: {e}",cid,True)
def run_over90(cid=None):
 try:
  tg("OVER 1.5 90% NAZIONI - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": data=[]
  now_dt=datetime.now(ROME); sel=[]; chk=0
  for fx in data:
   lg=fx.get("league",{}); co=lg.get("country")
   if co not in TOP: continue
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
   perc=get_best90(hid,aid)
   if perc=="LIMIT": time.sleep(60); perc=get_best90(hid,aid)
   if not perc: continue
   ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); ln=lg.get("name","")
   sel.append(f"{ora} [{co} - {ln}] {hn} vs {an} -> Over 1.5 @ {perc:.0f}%")
   if len(sel)>=20: break
  if sel:
   out=f"OVER 1.5 90% NAZIONI - {len(sel)} partite\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else: tg(f"0 partite 90% oggi. Controllate {chk}",cid,True)
 except Exception as e: tg(f"Errore Over90: {e}",cid,True)
def run_bolla(cid=None): tg("BOLLA - funzione vecchia mantenuta, usa OVER 1.5 90% per nuova versione",cid,True)
def run_doppia(cid=None):
 try:
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  out=[]; tg("Cerco DOPPIA...",cid,True)
  for fx in data:
   lg=fx.get("league",{}); co=lg.get("country")
   if co not in TOP: continue
   if lg.get("id")!=TOP.get(co): continue
   if is_youth(lg.get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   fid=fx.get("fixture",{}).get("id"); odd=get_over_odd(fid)
   if odd is None or odd>1.55: continue
   ora=str(fx.get("fixture",{}).get("date",""))[11:16]
   tm=fx.get("teams",{}); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); ln=lg.get("name","")
   out.append(f"{ora} [{co} - {ln}] {hn} vs {an} OVER 1.5 @ {odd}")
   time.sleep(0.3)
   if len(out)>=15: break
  if out:
   txt="DOPPIA "+str(len(out))+" OVER 1.5\n\n"
   for i,m in enumerate(out,1): txt+=f"{i}. {m}\n"
   tg(txt,cid,True)
  else: tg("Nessuna DOPPIA oggi",cid,True)
 except Exception as e: tg(f"Errore doppia {e}",cid,True)
def get_gialli_avg_team(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
  if data=="LIMIT": return "LIMIT"
  if not data or len(data)<5: return None
  tot=0; cnt=0
  for fx in data[:10]:
   fid=fx.get("fixture",{}).get("id")
   st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
   if st=="LIMIT": return "LIMIT"
   if not st: continue
   for ts in st:
    if str(ts.get("team",{}).get("id"))!=str(team_id): continue
    found=False; yc=0
    for x in ts.get("statistics",[]):
     if "yellow" in (x.get("type") or "").lower():
      found=True
      try: yc+=int(str(x.get("value") or 0))
      except: pass
    if found:
     cnt+=1
     if yc>=1: tot+=1
   time.sleep(0.25)
  if cnt<3: return None
  return tot/cnt*100
 except: return None
def run_gialli(cid=None):
 try:
  tg("GIALLI 65% WORLDWIDE - Analizzo 200 partite...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": data=[]
  now_dt=datetime.now(ROME); eligible=[]
  for fx in data:
   lg=fx.get("league",{})
   if is_youth(lg.get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try:
    fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
    fdt=datetime.fromisoformat(fd).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   eligible.append((fdt,fx))
  sel=[]; chk=0
  for fdt,fx in eligible[:200]:
   lg=fx.get("league",{}); co=lg.get("country"); chk+=1
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   g1=get_gialli_avg_team(hid)
   if g1=="LIMIT": time.sleep(60); g1=get_gialli_avg_team(hid)
   if not isinstance(g1,float): continue
   time.sleep(0.4)
   g2=get_gialli_avg_team(aid)
   if g2=="LIMIT": time.sleep(60); g2=get_gialli_avg_team(aid)
   if not isinstance(g2,float): continue
   avg=(g1+g2)/2
   if avg>=65:
    ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); ln=lg.get("name","")
    sel.append(f"{ora} [{co} - {ln}] {hn} vs {an} -> Gialli {avg:.0f}%")
    if len(sel)>=15: break
  if sel:
   out=f"GIALLI 65% - {len(sel)} partite su {chk}\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n"
   tg(out,cid,True)
  else: tg(f"0 partite gialli 65% oggi. Controllate {chk} su {len(eligible)} nel mondo",cid,True)
 except Exception as e: tg(f"Errore Gialli: {e}",cid,True)
def get_builder_odds(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT": return None
  odds={}
  for book in data[0].get("bookmakers",[])[:4]:
   for bet in book.get("bets",[]):
    bname=bet.get("name","")
    for v in bet.get("values",[]):
     try: o=float(v.get("odd"))
     except: continue
     val=v.get("value","")
     if "Over 1.5" in val and "o15" not in odds: odds["o15"]=o
     if "Yes" in val and "Both Teams" in bname and "gg" not in odds: odds["gg"]=o
     if "Over 4.5" in val and "Corners" in bname and "o45c" not in odds: odds["o45c"]=o
     if "Over 6.5" in val and "Corners" in bname and "o65c" not in odds: odds["o65c"]=o
  return odds
 except: return None
def build_builder_combo(odds):
 combos=[]
 if "o15" in odds and "gg" in odds:
  tot=odds["o15"]*odds["gg"]
  if 1.65 <= tot <= 2.1: combos.append((tot,f"OVER 1.5 ({odds['o15']}) + GG ({odds['gg']}) = {tot:.2f}"))
 if "o15" in odds and "o45c" in odds:
  tot=odds["o15"]*odds["o45c"]
  if 1.65 <= tot <= 2.1: combos.append((tot,f"OVER 1.5 + OVER 4.5 Angoli = {tot:.2f}"))
 if "o65c" in odds:
  if 1.65 <= odds["o65c"] <= 2.1: combos.append((odds["o65c"],f"OVER 6.5 Angoli = {odds['o65c']:.2f}"))
 combos.sort(key=lambda x: abs(x[0]-1.82))
 return combos[0] if combos else None
def run_bad_builder(cid=None):
 try:
  tg("BAD BUILDER 1.82 WORLDWIDE - GIORNO E NOTTE - Cerco in TUTTO IL MONDO...",cid,True)
  now_rome=datetime.now(ROME); dates=[]
  for i in range(3): d=(now_rome+timedelta(days=i)).strftime("%Y-%m-%d"); dates.append(d)
  sel=[]
  for date in dates:
   data=api(f"https://v3.football.api-sports.io/fixtures?date={date}") or []
   if data=="LIMIT": time.sleep(60); continue
   for fx in data:
    if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
    lg=fx.get("league",{})
    if is_youth(lg.get("name","")): continue
    fid=fx.get("fixture",{}).get("id"); tm=fx.get("teams",{}); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); co=lg.get("country"); ln=lg.get("name")
    try:
     fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
     fdt=datetime.fromisoformat(fd).astimezone(ROME); ora=fdt.strftime("%d/%m %H:%M")
    except: ora=date
    odds=get_builder_odds(fid)
    if not odds or len(odds)<2: time.sleep(0.2); continue
    combo=build_builder_combo(odds)
    if combo:
     tot,desc=combo; sel.append(f"{ora} [{co} - {ln}] {hn} vs {an}\n -> {desc}")
    time.sleep(0.3)
    if len(sel)>=15: break
   if len(sel)>=15: break
  if sel:
   out=f"BAD BUILDER 1.82 WORLDWIDE - {len(sel)} partite (MONDO)\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n\n"
   tg(out,cid,True)
  else: tg("0 partite builder trovate in tutto il mondo adesso",cid,True)
 except Exception as e: tg(f"Errore Builder: {e}",cid,True)
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
     if last_id in seen: continue
     seen.add(last_id)
     if len(seen)>500: seen.clear()
     msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     if "apri menu" in low: tg("Menu aperto FULL + OVER 1.5 90%",cid,True,False); continue
     if "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     if "accendi" in low or "/start" in low: is_paused=False; tg("V57.1 FINALE - PREPARATI 30-45 + BOM
