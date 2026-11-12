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

def run_basket(cid=None):
 try:
  tg("BASKET HANDICAP 12+ - Analizzo...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  games=apiB("games",{"date":today}) or []
  if games=="LIMIT": time.sleep(60); games=apiB("games",{"date":today}) or []
  sel=[]
  import re
  for g in games:
   if not isinstance(g,dict): continue
   gid=g.get("id")
   if not gid: continue
   st=g.get("status",{}).get("short","")
   if st not in ["NS",""]: continue
   odds=apiB("odds",{"game":gid}) or []
   if odds=="LIMIT": time.sleep(30); odds=apiB("odds",{"game":gid}) or []
   for item in odds:
    for book in item.get("bookmakers",[])[:2]:
     for bet in book.get("bets",[]):
      if "handicap" not in (bet.get("name") or "").lower(): continue
      for v in bet.get("values",[]):
       lab=v.get("value") or ""
       nums=re.findall(r"[-+]?\d+(?:\.\d+)?",lab)
       if not nums: continue
       try: line=float(nums[-1])
       except: continue
       if abs(line) < HMIN: continue
       try: q=float(v.get("odd"))
       except: continue
       home=g.get("teams",{}).get("home",{}).get("name","?"); away=g.get("teams",{}).get("away",{}).get("name","?")
       try:
        dt=g.get("date","").replace("Z","+00:00"); fdt=datetime.fromisoformat(dt).astimezone(ROME); ora=fdt.strftime("%H:%M")
       except: ora="oggi"
       sel.append(f"{ora} {home} vs {away}\n{lab} @ {q} (H {line})")
       if len(sel)>=15: break
    if len(sel)>=15: break
   if len(sel)>=15: break
  if sel:
   out=f"BASKET HANDICAP {HMIN}+ - {len(sel)}\n\n"
   for i,m in enumerate(sel,1): out+=f"{i}. {m}\n\n"
   tg(out,cid,True)
  else: tg(f"0 handicap {HMIN}+ oggi",cid,True)
 except Exception as e: tg(f"Errore Basket: {e}",cid,True)

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
     if "accendi" in low or "/start" in low: is_paused=False; tg("V66 ATTIVO - CALCIO+BASKET",cid,True); continue
     if "status" in low: tg(f"V66 CALCIO+BASKET - BUILDER {len(av_builder)} LIVE {len(av_g)}",cid,True); continue
     if "over 1.5" in low and "90" in low: run_over90(cid); continue
     if "over 3.5" in low: run_over35(cid); continue
     if "builder" in low: run_builder(cid); continue
     if "basket" in low or "handicap" in low: run_basket(cid); continue
  except: pass
  time.sleep(2)

def live_loop():
 tg("BOT V66 LIVE - V64 RIPRISTINATO + BASKET H12",None,True)
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

def scheduler_loop():
 while True:
  try:
   now=datetime.now(ROME)
   if now.hour==8 and now.minute==0:
    if not is_paused:
     run_over90(); time.sleep(3); run_over35(); time.sleep(3); run_builder(); time.sleep(3); run_basket()
    time.sleep(70)
  except: pass
  time.sleep(20)

threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
threading.Thread(target=builder_tracker,daemon=True).start()
threading.Thread(target=scheduler_loop,daemon=True).start()
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
