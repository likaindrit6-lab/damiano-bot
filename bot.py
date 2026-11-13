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
PAESI=["Italy","England","Spain","Germany","France","Netherlands","Portugal","Belgium","Turkey","Scotland","Austria","Switzerland","Denmark","Sweden","Norway","Poland","Czech Republic","Croatia","Serbia","Greece","Romania","Bulgaria","Hungary","Slovakia","Slovenia","Ireland","Wales","Finland","Iceland","Cyprus","Malta","Luxembourg","Belarus","Russia"]

def is_youth(n):
 b=n.lower()
 return any(x in b for x in ["u19","u21","u23","u17","women","youth","reserve","futsal"])

app=Flask(__name__)
@app.route("/")
def home():
 return "V54.5 FINALE FULL",200

TAST=json.dumps({"keyboard":[["OVER 1.5 90% NAZIONI"],["GIALLI 85%"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["CALCIO D'ANGOLO +6"],["BAD BUILDER 1.82 WORLDWIDE"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_C=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})

def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not BOT or not cid: return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys:
   pay["reply_markup"]=json.loads(TAST_C) if chiusa else json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except Exception as e:
  print(e)

def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except:
  return []

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

def get_last10_over(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
  if data=="LIMIT": return "LIMIT"
  if not data or len(data)<4: return None
  c=sum(1 for f in data if (f.get("goals",{}).get("home") or 0)+(f.get("goals",{}).get("away") or 0)>=2)
  return c/len(data)*100
 except: return None

def get_best90(hid,aid):
 try:
  s1=get_last10_over(hid)
  if s1=="LIMIT": return "LIMIT"
  time.sleep(0.35)
  s2=get_last10_over(aid)
  if s2=="LIMIT": return "LIMIT"
  if s1 is None or s2 is None: return None
  return (s1+s2)/2
 except: return None

def get_corner_avg(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
  if data=="LIMIT": return "LIMIT"
  if not data or len(data)<3: return None
  tot=cnt=0
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
  if cnt<3: return None
  return tot/cnt
 except: return None

def get_gialli_avg(team_id):
 try:
  u=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
  data=api(u)
  if data=="LIMIT": return "LIMIT"
  if not data or len(data)<4: return None
  ok=tot=0
  for fx in data[:10]:
   fid=fx.get("fixture",{}).get("id")
   st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
   if st=="LIMIT": return "LIMIT"
   if not st: continue
   yell=0
   for ts in st:
    if ts.get("team",{}).get("id")==team_id:
     for x in ts.get("statistics",[]):
      if "yellow" in (x.get("type") or "").lower():
       try: yell=int(str(x.get("value") or 0))
       except: pass
   if yell>=1: ok+=1
   tot+=1
   time.sleep(0.2)
  if tot<4: return None
  return ok/tot*100
 except: return None

def run_over90(cid=None):
 try:
  tg("OVER 1.5 90% - Analizzo 80 partite...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": tg("API LIMIT 429 - riprova tra 10 min",cid,True); return
  now_dt=datetime.now(ROME); sel=[]; chk=0
  for fx in data:
   if fx.get("league",{}).get("country") not in PAESI: continue
   if is_youth(fx.get("league",{}).get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try: fdt=datetime.fromisoformat(fx.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   chk+=1
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   perc=get_best90(hid,aid)
   if perc=="LIMIT": time.sleep(60); perc=get_best90(hid,aid)
   if not perc or perc<80: continue
   ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); ln=fx.get("league",{}).get("name")
   sel.append((perc,f"{ora} [{fx.get('league',{}).get('country')} - {ln}] {hn} vs {an} -> {perc:.0f}%"))
   if len(sel)>=20 or chk>80: break
  sel.sort(key=lambda x: x[0], reverse=True)
  if sel: tg(f"OVER 1.5 80%+ - {len(sel)} partite (su {chk})\n\n"+"\n".join([f"{i}. {m[1]}" for i,m in enumerate(sel,1)]),cid,True)
  else: tg(f"0 partite 80%+ - controllate {chk} su {len(data)}",cid,True)
 except Exception as e: tg(f"Errore Over {e}",cid,True)

def run_gialli(cid=None):
 try:
  tg("GIALLI 85% - Analizzo 35 partite, 3 min...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": tg("API LIMIT",cid,True); return
  now_dt=datetime.now(ROME); sel=[]; chk=0
  for fx in data:
   if fx.get("league",{}).get("country") not in PAESI: continue
   if is_youth(fx.get("league",{}).get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try: fdt=datetime.fromisoformat(fx.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   chk+=1
   if chk>35: break
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   g1=get_gialli_avg(hid)
   if g1=="LIMIT": time.sleep(60); g1=get_gialli_avg(hid)
   time.sleep(0.3)
   g2=get_gialli_avg(aid)
   if g2=="LIMIT": time.sleep(60); g2=get_gialli_avg(aid)
   if not g1 or not g2: continue
   avg=(g1+g2)/2
   if avg<75: continue
   ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
   sel.append((avg,f"{ora} [{fx.get('league',{}).get('country')}] {hn} vs {an} -> Gialli {avg:.0f}%"))
  sel.sort(key=lambda x: x[0], reverse=True)
  if sel: tg(f"GIALLI 85% - {len(sel)} partite (su {chk})\n\n"+"\n".join([f"{i}. {m[1]}" for i,m in enumerate(sel,1)]),cid,True)
  else: tg(f"0 gialli 75%+ - controllate {chk}",cid,True)
 except Exception as e: tg(f"Errore Gialli {e}",cid,True)

def run_bolla(cid=None):
 try:
  tg("BOLLA EUROPA - TOP 5 - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME); sel=[]
  for fx in data:
   if fx.get("league",{}).get("country") not in PAESI: continue
   if is_youth(fx.get("league",{}).get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try: fdt=datetime.fromisoformat(fx.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   perc=get_best90(hid,aid)
   if perc=="LIMIT": time.sleep(60); perc=get_best90(hid,aid)
   if not perc or perc<82: continue
   ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); ln=fx.get("league",{}).get("name")
   sel.append((perc,f"{ora} [{fx.get('league',{}).get('country')} - {ln}] {hn} vs {an} {perc:.0f}%"))
   if len(sel)>=30: break
  sel.sort(key=lambda x: x[0], reverse=True)
  if sel: tg(f"BOLLA TOP 5 ({len(sel)} trovate)\n\n"+"\n".join([f"{i}. {m[1]}" for i,m in enumerate(sel[:5],1)]),cid,True)
  else: tg("0 partite per bolla oggi",cid,True)
 except Exception as e: tg(f"Errore Bolla {e}",cid,True)

def run_doppia(cid=None):
 try:
  tg("DOPPIA - Cerco...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  out=[]
  for fx in data:
   if fx.get("league",{}).get("country") not in PAESI: continue
   if is_youth(fx.get("league",{}).get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   fid=fx.get("fixture",{}).get("id")
   odd=get_over_odd(fid)
   if odd is None or odd>1.55: continue
   ora=str(fx.get("fixture",{}).get("date",""))[11:16]
   tm=fx.get("teams",{}); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name"); ln=fx.get("league",{}).get("name")
   out.append(f"{ora} [{fx.get('league',{}).get('country')} - {ln}] {hn} vs {an} @ {odd}")
   time.sleep(0.2)
   if len(out)>=15: break
  tg("DOPPIA "+str(len(out))+"\n\n"+"\n".join([f"{i}. {m}" for i,m in enumerate(out,1)]) if out else "Nessuna DOPPIA oggi",cid,True)
 except Exception as e: tg(f"Errore doppia {e}",cid,True)

def run_corner(cid=None):
 try:
  tg("OVER 6.5 ANGOLI - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  now_dt=datetime.now(ROME); sel=[]; chk=0
  for fx in data:
   if fx.get("league",{}).get("country") not in PAESI: continue
   if is_youth(fx.get("league",{}).get("name","")): continue
   if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try: fdt=datetime.fromisoformat(fx.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
   except: continue
   if fdt<now_dt: continue
   chk+=1
   if chk>12: break
   tm=fx.get("teams",{}); hid=tm.get("home",{}).get("id"); aid=tm.get("away",{}).get("id")
   c1=get_corner_avg(hid)
   if c1=="LIMIT": time.sleep(60); c1=get_corner_avg(hid)
   if not c1: continue
   time.sleep(0.3)
   c2=get_corner_avg(aid)
   if c2=="LIMIT": time.sleep(60); c2=get_corner_avg(aid)
   if not c2: continue
   avg=(c1+c2)/2
   if avg>=6.5:
    ora=fdt.strftime("%H:%M"); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
    sel.append((avg,f"{ora} [{fx.get('league',{}).get('country')}] {hn} vs {an} -> {avg:.1f}"))
  if sel:
   sel.sort(key=lambda x: x[0], reverse=True)
   tg(f"OVER 6.5 ANGOLI - {len(sel)} partite\n\n"+"\n".join([f"{i}. {m[1]}" for i,m in enumerate(sel,1)]),cid,True)
  else: tg(f"0 partite Over 6.5 - {chk} analizzate",cid,True)
 except Exception as e: tg(f"Errore Corner {e}",cid,True)

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
     if "Over 6.5" in val and "Corners" in bname and "o65c" not in odds: odds["o65c"]=o
  return odds
 except: return None

def build_combo(odds):
 combos=[]
 if "o15" in odds and "gg" in odds:
  tot=odds["o15"]*odds["gg"]
  if 1.65 <= tot <= 2.1: combos.append((tot,f"OVER 1.5 + GG = {tot:.2f}"))
 if "o65c" in odds:
  if 1.65 <= odds["o65c"] <= 2.1: combos.append((odds["o65c"],f"OVER 6.5 Angoli = {odds['o65c']:.2f}"))
 combos.sort(key=lambda x: abs(x[0]-1.82))
 return combos[0] if combos else None

def run_builder(cid=None):
 try:
  tg("BAD BUILDER 1.82 WORLDWIDE - Cerco...",cid,True)
  now_rome=datetime.now(ROME); sel=[]
  for d in [(now_rome+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]:
   data=api(f"https://v3.football.api-sports.io/fixtures?date={d}") or []
   if data=="LIMIT": time.sleep(60); continue
   for fx in data:
    if fx.get("fixture",{}).get("status",{}).get("short")!="NS": continue
    if is_youth(fx.get("league",{}).get("name","")): continue
    fid=fx.get("fixture",{}).get("id")
    tm=fx.get("teams",{}); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
    co=fx.get("league",{}).get("country"); ln=fx.get("league",{}).get("name")
    try: ora=datetime.fromisoformat(fx.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME).strftime("%d/%m %H:%M")
    except: ora=d
    odds=get_builder_odds(fid)
    if not odds or len(odds)<2: time.sleep(0.2); continue
    combo=build_combo(odds)
    if combo: sel.append(f"{ora} [{co} - {ln}] {hn} vs {an}\n -> {combo[1]}")
    time.sleep(0.3)
    if len(sel)>=15: break
   if len(sel)>=15: break
  tg(f"BAD BUILDER - {len(sel)} partite\n\n"+"\n\n".join([f"{i}. {m}" for i,m in enumerate(sel,1)]) if sel else "0 partite builder",cid,True)
 except Exception as e: tg(f"Errore Builder {e}",cid,True)

def poll():
 global last_id,is_paused
 try:
  if BOT: requests.get(f"https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(20); continue
   base="https://api.telegram.org/bot"+BOT
   url=base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20"
   r=requests.get(url,timeout=35).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     if "apri menu" in low: tg("Menu aperto V54.5 FINALE",cid,True,False); continue
     if "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     if "accendi" in low or "/start" in low: is_paused=False; tg("V54.5 FINALE FULL ATTIVO",cid,True); continue
     if "status" in low: tg("STATUS V54.5 OK - TUTTO DENTRO",cid,True); continue
     if "over 1.5" in low: run_over90(cid); continue
     if "gialli" in low: run_gialli(cid); continue
     if "bolla" in low: run_bolla(cid); continue
     if "doppia" in low: run_doppia(cid); continue
     if "angolo" in low and "builder" not in low: run_corner(cid); continue
     if "builder" in low: run_builder(cid); continue
  except: pass
  time.sleep(2)

def live_loop():
 tg("BOT V54.5 FINALE FULL ATTIVO",None,True)
 while True:
  try:
   if is_paused: time.sleep(30); continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6: time.sleep(300); continue
   games=api("https://v3.football.api-sports.io/fixtures?live=all")
   if games=="LIMIT": time.sleep(3600); continue
   if not games: time.sleep(60); continue
   for g in games:
    fid=g.get("fixture",{}).get("id"); mm=g.get("fixture",{}).get("status",{}).get("elapsed")
    if mm is None: continue
    gh=g.get("goals",{}).get("home"); ga=g.get("goals",{}).get("away")
    tm=g.get("teams",{}); home=tm.get("home",{}).get("name"); away=tm.get("away",{}).get("name")
    lg=g.get("league",{}); label=f"[{lg.get('country','')} - {lg.get('name','')}]"
    if fid not in av_sfiga_score: av_sfiga_score[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga_score[fid]
     if gh!=oh or ga!=oa:
      chi="HOME" if gh>oh else "AWAY"; av_sfiga_score[fid]=(gh,ga)
      sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       if chi==tipo:
        sg=gh if tipo=="HOME" else ga; fg=ga if tipo=="HOME" else gh
        if sg>=fg:
         stato="PAREGGIA" if sg==fg else "VANTAGGIO"
         ns=home if tipo=="HOME" else away; nf=away if tipo=="HOME" else home
         tg(f"⚫ SFIGATA {stato} {mm}' {label} {home} {gh}-{ga} {away}\nSfigata {ns} @{qs}\nFavorita {nf} @{qf}")
    if 30<=mm<=45 and fid not in av_s_first:
     st=api("https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid))
     sot=cor=0
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
      tg(f"🔥 PREPARATI {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{cor}")
      av_s_first.add(fid)
    if 65<=mm<=90 and fid not in av_s:
     st=api("https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid))
     sot=cor=0
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
      tg(f"🚀 GIOCALO {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{cor}")
      av_s.add(fid); av_g[fid]=gh+ga
   for g in games:
    fid=g.get("fixture",{}).get("id")
    if fid in av_g:
     gh2=g.get("goals",{}).get("home"); ga2=g.get("goals",{}).get("away")
     if gh2+ga2>av_g[fid]:
      lg=g.get("league",{}); label=f"[{lg.get('country','')} - {lg.get('name','')}]"
      tm=g.get("teams",{}); hn=tm.get("home",{}).get("name"); an=tm.get("away",{}).get("name")
      tg(f"🟢 GOAL VINTO! {label} {hn} {gh2}-{ga2} {an}"); del av_g[fid]
   time.sleep(60)
  except Exception as e: print(e); time.sleep(15)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
