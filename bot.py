   if not isinstance(g2,float):
    continue
   avg=(g1+g2)/2
   if avg>=65:
    ora=fdt.strftime("%H:%M")
    hn=tm.get("home",{}).get("name")
    an=tm.get("away",{}).get("name")
    ln=lg.get("name","")
    sel.append((f"{ora} [{co} - {ln}] {hn} vs {an} -> Gialli {avg:.0f}%",hn,an))
    if len(sel)>=15:
     break
  if sel:
   out=f"GIALLI 65% - {len(sel)} partite\n\n"
   for i,(m,hn,an) in enumerate(sel,1):
    out+=f"{i}. {m}\n"
   tg_inline(out,None,cid)
  else:
   tg(f"0 partite gialli 65% oggi. Controllate {chk} su {len(eligible)} nel mondo",cid,True)
 except Exception as e:
  tg(f"Errore Gialli: {e}",cid,True)

# --- BAD BUILDER WORLDWIDE GIORNO E NOTTE ---
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
  for dt in dates:
   data=api(f"https://v3.football.api-sports.io/fixtures?date={dt}") or []
   if data=="LIMIT":
    time.sleep(60)
    continue
   for fx in data:
    if fx.get("fixture",{}).get("status",{}).get("short")!="NS":
     continue
    lg=fx.get("league",{})
    if is_youth(lg.get("name","")):
     continue
    fid=fx.get("fixture",{}).get("id")
    tm=fx.get("teams",{})
    hn=tm.get("home",{}).get("name")
    an=tm.get("away",{}).get("name")
    co=lg.get("country")
    ln=lg.get("name")
    try:
     fd=fx.get("fixture",{}).get("date","").replace("Z","+00:00")
     fdt=datetime.fromisoformat(fd).astimezone(ROME)
     ora=fdt.strftime("%d/%m %H:%M")
    except:
     ora=dt
    odds=get_builder_odds(fid)
    if not odds or len(odds)<2:
     time.sleep(0.2)
     continue
    combo=build_builder_combo(odds)
    if combo:
     tot,desc=combo
     sel.append((f"{ora} [{co} - {ln}] {hn} vs {an}\n -> {desc}",hn,an))
    time.sleep(0.3)
    if len(sel)>=15:
     break
   if len(sel)>=15:
    break
  if sel:
   out=f"BAD BUILDER 1.82 WORLDWIDE - {len(sel)} partite (MONDO)\n\n"
   for i,(m,hn,an) in enumerate(sel,1):
    out+=f"{i}. {m}\n\n"
   tg_inline(out,None,cid)
  else:
   tg("0 partite builder trovate in tutto il mondo adesso",cid,True)
 except Exception as e:
  tg(f"Errore Builder: {e}",cid,True)

# --- BASKET HANDICAP 12+ (The Odds API) ---
_basket_cache={}
_basket_cache_time=0
_basket_alert_sent=set()

LEAGUE_NAMES={
 "basketball_nba":"NBA",
 "basketball_euroleague":"Eurolega",
 "basketball_eurocup":"Eurocup",
 "basketball_ncaab":"NCAAB",
 "basketball_wnba":"WNBA",
 "basketball_spain_liga_acb":"Liga ACB",
 "basketball_italy_lega_serie_a":"Serie A",
 "basketball_turkey_bsl":"BSL Turkey",
 "basketball_greece_heba_a1":"HEBA A1",
 "basketball_france_lnb_pro_a":"LNB Pro A",
 "basketball_germany_bbl":"BBL Germany",
 "basketball_brazil_nbb":"NBB Brazil",
 "basketball_argentina_liga_nacional":"Liga Nacional",
 "basketball_china_cba":"CBA China",
 "basketball_japan_b_league":"B-League Japan",
 "basketball_korea_kbl":"KBL Korea",
 "basketball_philippines_pba":"PBA Philippines",
 "basketball_portugal_liga_betclic":"Liga Portugal",
 "basketball_adriatic_liga":"ABA Liga",
 "basketball_vtb_united_league":"VTB United",
}

def odds_api(url):
 try:
  r=requests.get(url,timeout=20)
  if r.status_code==429:
   return []
  data=r.json()
  if isinstance(data,str):
   try:
    data=json.loads(data)
   except:
    return []
  if isinstance(data,list):
   return data
  return []
 except:
  return []

def get_all_basketball_sports():
 try:
  url=f"https://api.the-odds-api.com/v4/sports/?apiKey={ODDS_KEY or ''}"
  data=odds_api(url)
  if isinstance(data,str):
   try:
    data=json.loads(data)
   except:
    data=[]
  if not isinstance(data,list):
   return []
  sports=[]
  for sp in data:
   if not isinstance(sp,dict):
    continue
   key=sp.get("key","")
   if not isinstance(key,str):
    continue
   if key.startswith("basketball_"):
    sports.append(key)
  return sports
 except:
  return []

def get_basket_games_today():
 today_str=datetime.now(ROME).strftime("%Y-%m-%d")
 all_games=[]
 total_api=0
 sports=get_all_basketball_sports()
 total_leagues=len(sports)
 for sport in sports:
  url=f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={ODDS_KEY or ''}&regions=eu,us,uk,au&markets=spreads,alternate_spreads,h2h,spreads_alt&oddsFormat=decimal"
  data=odds_api(url)
  if isinstance(data,str):
   try:
    data=json.loads(data)
   except:
    data=[]
  if not isinstance(data,list) or not data:
   time.sleep(0.2)
   continue
  total_api+=len(data)
  for gm in data:
   if not isinstance(gm,dict):
    continue
   ct=gm.get("commence_time","")
   if not isinstance(ct,str):
    continue
   if not ct.startswith(today_str):
    continue
   gm["_sport_key"]=sport
   all_games.append(gm)
  time.sleep(0.2)
 return all_games,total_api,total_leagues

def check_handicap_12_market(game):
 if not isinstance(game,dict):
  return False,None,None,None
 best_line=None
 best_odd=None
 best_team=None
 for bm in game.get("bookmakers",[]):
  if not isinstance(bm,dict):
   continue
  for mkt in bm.get("markets",[]):
   if not isinstance(mkt,dict):
    continue
   mkey=mkt.get("key","")
   if mkey not in ("spreads","alternate_spreads","spreads_alt","hcap","alternate_hcap","asian_handicap","handicap"):
    continue
   for out in mkt.get("outcomes",[]):
    if not isinstance(out,dict):
     continue
    pt=out.get("point")
    if pt is None:
     continue
    try:
     pt=float(pt)
    except:
     continue
    if abs(pt)>=10.5:
     price=out.get("price")
     if price is None:
      continue
     try:
      pf=float(price)
     except:
      continue
     if best_odd is None or pf>best_odd:
      best_line=pt
      best_odd=pf
      best_team=out.get("name","")
 if best_line is not None:
  return True,best_line,best_odd,best_team
 return False,None,None,None

def _format_basket_date(ct):
 try:
  fdt=datetime.fromisoformat(ct.replace("Z","+00:00")).astimezone(ROME)
  return fdt
 except:
  return None

def run_basket_handicap(cid=None):
 try:
  tg("🏀 BASKET HANDICAP 12+ - Analizzo TUTTO il mondo...",cid,True)
  sports_url=f"https://api.the-odds-api.com/v4/sports/?apiKey={ODDS_KEY or ''}"
  sports_data=odds_api(sports_url)
  if isinstance(sports_data,str):
   try:
    sports_data=json.loads(sports_data)
   except:
    sports_data=[]
  if not isinstance(sports_data,list):
   sports_data=[]
  basket_keys=[]
  for s in sports_data:
   if not isinstance(s,dict):
    continue
   key=s.get("key","")
   if isinstance(key,str) and "basketball" in key:
    basket_keys.append(key)
  tg(f"DEBUG: Ho trovato {len(basket_keys)} campionati basket mondiali: {basket_keys[:10]}",cid,True)
  total_games=0
  found_games=[]
  all_points=[]
  for key in basket_keys:
   url=f"https://api.the-odds-api.com/v4/sports/{key}/odds/?apiKey={ODDS_KEY or ''}&regions=eu,us,uk,au&markets=spreads&oddsFormat=decimal"
   data=odds_api(url)
   if isinstance(data,str):
    try:
     data=json.loads(data)
    except:
     data=[]
   if not isinstance(data,list):
    continue
   total_games+=len(data)
   for game in data:
    if not isinstance(game,dict):
     continue
    for book in game.get("bookmakers",[]):
     if not isinstance(book,dict):
      continue
     for market in book.get("markets",[]):
      if not isinstance(market,dict):
       continue
      for outcome in market.get("outcomes",[]):
       if not isinstance(outcome,dict):
        continue
       pt=outcome.get("point")
       if pt is not None:
        try:
         fp=float(pt)
         all_points.append(fp)
         if fp>=10.5 or fp<=-10.5:
          if game not in found_games:
           found_games.append(game)
        except:
         pass
    time.sleep(0.15)
  if all_points:
   pts_str=f"min {min(all_points)} max {max(all_points)} - Esempi: {all_points[:20]}"
  else:
   pts_str="nessuno"
  tg(f"DEBUG: Controllate {total_games} partite totali nel mondo. Punti handicap trovati: {pts_str}",cid,True)
  _basket_cache["games"]=found_games
  _basket_cache["date"]=datetime.now(ROME).strftime("%Y-%m-%d")
  _basket_cache_time=time.time()
  if not found_games:
   tg(f"VERO: Su {total_games} partite in {len(basket_keys)} campionati, 0 con +12. Questo e il dato reale API. Se e 0 e problema API, non mio.",cid,True)
   return
  data_str=datetime.now(ROME).strftime("%d/%m/%Y")
  out=f"🏀 BASKET HANDICAP +12 - Partite di oggi [{data_str}]\n"
  out+=f"📊 Controllati {len(basket_keys)} campionati, {total_games} partite totali API\n\n"
  rows=[]
  for g in found_games[:20]:
   if not isinstance(g,dict):
    continue
   home=g.get("home_team","?")
   away=g.get("away_team","?")
   ct=g.get("commence_time","")
   fdt=_format_basket_date(ct)
   ora=fdt.strftime("%H:%M") if fdt else "?"
   best_line=None
   best_odd=None
   for book in g.get("bookmakers",[]):
    if not isinstance(book,dict):
     continue
    for market in book.get("markets",[]):
     if not isinstance(market,dict):
      continue
     for outcome in market.get("outcomes",[]):
      if not isinstance(outcome,dict):
       continue
      pt=outcome.get("point")
      if pt is None:
       continue
      try:
       fp=float(pt)
      except:
       continue
      if abs(fp)>=10.5:
       price=outcome.get("price")
       try:
        pprice=float(price) if price else None
       except:
        pprice=None
       if best_odd is None or (pprice and pprice>best_odd):
        best_line=fp
        best_odd=pprice
   sign="+" if best_line and best_line>0 else ""
   line_str=f"{sign}{best_line}" if best_line is not None else "?"
   if best_odd:
    out+=f"⏰ {ora} - {home} vs {away} | Spread {line_str} @ {best_odd:.2f}\n"
   else:
    out+=f"⏰ {ora} - {home} vs {away} | Spread {line_str}\n"
  tg_inline(out,None,cid)
 except Exception as e:
  tg(f"ERRORE DEBUG: {e}",cid,True)

def check_basket_alert():
 while True:
  try:
   if is_paused:
    time.sleep(60)
    continue
   today_str=datetime.now(ROME).strftime("%Y-%m-%d")
   cache_age=time.time()-_basket_cache_time
   cached=_basket_cache.get("games",[])
   if _basket_cache.get("date")==today_str and cache_age<600 and isinstance(cached,list):
    games=cached
   else:
    games,_,_=get_basket_games_today()
    _basket_cache["games"]=games
    _basket_cache["date"]=today_str
   now=datetime.now(ROME)
   for gm in games:
    if not isinstance(gm,dict):
     continue
    gid=gm.get("id","")
    if gid in _basket_alert_sent:
     continue
    found,line,odd,team=check_handicap_12_market(gm)
    if not found:
     continue
    ct=gm.get("commence_time","")
    fdt=_format_basket_date(ct)
    if not fdt:
     continue
    diff=(fdt-now).total_seconds()/60
    if 14<=diff<=16:
     ora=fdt.strftime("%H:%M")
     home=gm.get("home_team","?")
     away=gm.get("away_team","?")
     sk=gm.get("_sport_key","")
     league=LEAGUE_NAMES.get(sk,sk.replace("basketball_","").upper()) if sk else "?"
     sign="+" if line>0 else ""
     msg=f"⚠️ TRA 15 MINUTI - 🏀 {league} {home} vs {away} - Handicap {sign}{line} @ {odd:.2f}"
     tg_inline(msg,[goldbet_button(home,away)])
     _basket_alert_sent.add(gid)
  except Exception as e:
   print(e)
  time.sleep(60)

def acquire_single_instance():
 f=open("/tmp/bot_v76.lock","w")
 try:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  return f
 except OSError:
  f.close()
  return None
def poll():
 global is_paused,last_id
 try:
  if BOT:
   requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
 except:
  pass
 while True:
  try:
   if not BOT:
    time.sleep(20)
    continue
   base="https://api.telegram.org/bot"+BOT
   url=base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     if last_id in seen:
      continue
     seen.add(last_id)
     msg=u.get("message",{})
     txt=(msg.get("text") or "").strip()
     low=txt.lower()
     cid=msg.get("chat",{}).get("id")
     if not txt:
      continue
     if "spegni" in low:
      is_paused=True
      tg("PAUSA",cid)
      continue
     if "accendi" in low or "/start" in low:
      is_paused=False
      tg("V76 FULL ATTIVO + OVER 1.5 90% + BUILDER WORLDWIDE + BASKET 12+",cid)
      continue
     if "status" in low:
      tg("STATUS V76 FULL + BUILDER WORLDWIDE + BASKET HANDICAP 12+ OK",cid)
      continue
     if "basket" in low or "handicap" in low or "12+" in low:
      run_basket_handicap(cid)
      continue
     if "over 1.5" in low and "90" in low:
      run_over90(cid)
      continue
     if "bolla" in low:
      run_bolla(cid)
      continue
     if "doppia" in low:
      run_doppia(cid)
      continue
     if "gialli" in low:
      run_gialli(cid)
      continue
     if "angolo" in low and "builder" not in low:
      run_corner_over65(cid)
      continue
     if "builder" in low:
      run_bad_builder(cid)
      continue
  except:
   pass
  time.sleep(2)
def live_loop():
 tg("BOT V76 FULL + OVER 1.5 90% + BUILDER WORLDWIDE + BASKET 12+ ATTIVO",None)
 while True:
  try:
   if is_paused:
    time.sleep(30)
    continue
   now=datetime.now(ITALY)
   if 2<=now.hour<6:
    time.sleep(300)
    continue
   games=api("https://v3.football.api-sports.io/fixtures?live=all")
   if games=="LIMIT":
    time.sleep(3600)
    continue
   if not games:
    time.sleep(60)
    continue
   for g in games:
    fid=g.get("fixture",{}).get("id")
    mm=g.get("fixture",{}).get("status",{}).get("elapsed")
    if mm is None:
     continue
    gh=g.get("goals",{}).get("home")
    ga=g.get("goals",{}).get("away")
    tm=g.get("teams",{})
    home=tm.get("home",{}).get("name")
    away=tm.get("away",{}).get("name")
    lg=g.get("league",{})
    label=f"[{lg.get('country','')} - {lg.get('name','')}]"
    if fid not in av_sfiga_score:
     av_sfiga_score[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga_score[fid]
     if gh!=oh or ga!=oa:
      chi="HOME" if gh>oh else "AWAY"
      av_sfiga_score[fid]=(gh,ga)
      sf=None
      if lg.get("country") in TOP and fid not in av_sfiga_sent:
       sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       if chi==tipo:
        sg=gh if tipo=="HOME" else ga
        fg=ga if tipo=="HOME" else gh
        if sg>=fg:
         stato="PAREGGIA" if sg==fg else "VANTAGGIO"
         ns=home if tipo=="HOME" else away
         nf=away if tipo=="HOME" else home
         tg(f"⚫ SFIGATA {stato} {mm}' {label} {home} {gh}-{ga} {away}\nSfigata {ns} @{qs}\nFavorita {nf} @{qf}")
         av_sfiga_sent.add(fid)
    if 30<=mm<=45 and fid not in av_s_first:
     u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid)
     st=api(u)
     sot=0
     cor=0
     if st and len(st)>=2:
      for s in st:
       for x in s.get("statistics",[]):
        t=x.get("type","")
        if "Shots on Goal" in t:
         try:
          sot+=int(str(x.get("value") or 0))
         except:
          pass
        if "corner" in t.lower():
         try:
          cor+=int(str(x.get("value") or 0))
         except:
          pass
     if sot>=4 or cor>=6:
      tg(f"🔥 PREPARATI {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{cor}")
      av_s_first.add(fid)
    if 60<=mm<=85 and fid not in av_s and (gh,ga) in [(0,0),(1,0),(0,1),(1,1)]:
     sot=get_sot(fid)
     if sot is not None and sot>=7:
      dc="X2 + Multigol 1-5" if ga>gh else "1X + Multigol 1-5"
      tg_inline(f"🚀 GIOCALO {mm}' {label} {home} {gh}-{ga} {away} Tiri in porta:{sot}\n\n- Over 0.5 Gol (quota stimata 1.60)\n- Gioca: {dc} (quota stimata 1.70)",[goldbet_button(home,away)])
      av_s.add(fid)
      av_g[fid]=gh+ga
   for g in games:
    fid=g.get("fixture",{}).get("id")
    if fid in av_g:
     gh2=g.get("goals",{}).get("home")
     ga2=g.get("goals",{}).get("away")
     if gh2+ga2>av_g[fid]:
      lg=g.get("league",{})
      label=f"[{lg.get('country','')} - {lg.get('name','')}]"
      tm=g.get("teams",{})
      hn=tm.get("home",{}).get("name")
      an=tm.get("away",{}).get("name")
      tg(f"🟢 GOAL VINTO! {label} {hn} {gh2}-{ga2} {an}")
      del av_g[fid]
   time.sleep(60)
  except Exception as e:
   print(e)
   time.sleep(15)
def check_tripla_automatica():
 while True:
  time.sleep(90*60)
  try:
   if is_paused:
    continue
   games=api("https://v3.football.api-sports.io/fixtures?live=all")
   if not games or games=="LIMIT":
    continue
   cands=[]
   for g in games:
    fid=g.get("fixture",{}).get("id")
    sot=get_sot(fid)
    if sot is None or sot<7:
     continue
    tm=g.get("teams",{})
    lg=g.get("league",{})
    cands.append((sot,f"[{lg.get('country','')} - {lg.get('name','')}]",tm.get("home",{}).get("name"),tm.get("away",{}).get("name"),g.get("goals",{}).get("home"),g.get("goals",{}).get("away")))
   if len(cands)<=15:
    continue
   top=sorted(cands,key=lambda x:x[0],reverse=True)[:3]
   msg=f"🎯 TRIPLA AUTOMATICA DELLE {datetime.now(ROME).strftime('%H:%M')}\n\n"
   rows=[]
   for i,(sot,label,home,away,gh,ga) in enumerate(top,1):
    msg+=f"{i}. {label} {home} {gh}-{ga} {away} Tiri in porta:{sot}\n"
   tg_inline(msg,None)
  except Exception as e:
   print(e)
_LOCK=acquire_single_instance()
if _LOCK:
 threading.Thread(target=poll,daemon=True).start()
 threading.Thread(target=live_loop,daemon=True).start()
 threading.Thread(target=check_tripla_automatica,daemon=True).start()
 threading.Thread(target=check_basket_alert,daemon=True).start()
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)),use_reloader=False)
