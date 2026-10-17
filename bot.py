import os,time,requests,threading,json,urllib.parse
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
TOP_LEAGUES={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,"Belarus":116,"Russia":235}
def is_youth_league(name):
    n=name.lower()
    bad=["u19","u21","u23","u17","women"," w ","female","youth","reserve","development","academy"," u18"," u20"]
    for x in bad:
        if x in n: return True
    return False
app=Flask(__name__)
@app.route("/")
def home(): return "BOT V54 OK NAZIONI",200
TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["STATISTICHE 35 NAZIONI"],["CALCIO D'ANGOLO +6"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_CHIUSA=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False,chiusa=False,home=None,away=None):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  upper=m.upper()
  if "PREPARATI" in upper and "🔥" not in m: m=f"🔥 {m}"
  elif "GIOCALO" in upper and "🚀" not in m: m=f"🚀 {m}"
  elif any(x in upper for x in ["GOL","PAREGGIA","VANTAGGIO","GOAL VINTO"]) and "🟢" not in m: m=f"🟢 {m}"
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys: pay["reply_markup"]=json.loads(TAST_CHIUSA if chiusa else TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=25)
 except Exception as e: print(e)
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
def get_over_15(fid):
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
       except: continue
 except: pass
 return None
def get_fixtures_today():
 today=datetime.now(ROME).strftime("%Y-%m-%d")
 return api("https://v3.football.api-sports.io/fixtures?date="+today)
def get_last_10_stats(team_id):
  try:
    data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
    if not data or data=="LIMIT": return "LIMIT"
    over05=over15=over25=gg=0
    tot=len(data)
    if tot<5: return None
    for f in data:
      gh=f.get("goals",{}).get("home") or 0
      ga=f.get("goals",{}).get("away") or 0
      if gh+ga >=1: over05+=1
      if gh+ga >=2: over15+=1
      if gh+ga >=3: over25+=1
      if gh>=1 and ga>=1: gg+=1
    return {"tot":tot,"o05":over05/tot*100,"o15":over15/tot*100,"o25":over25/tot*100,"gg":gg/tot*100}
  except: return None
def get_best_stat_90(home_id,away_id):
  try:
    s1=get_last_10_stats(home_id)
    if s1=="LIMIT": return "LIMIT"
    time.sleep(0.35)
    s2=get_last_10_stats(away_id)
    if s2=="LIMIT": return "LIMIT"
    if not s1 or not s2: return None
    o05=(s1["o05"]+s2["o05"])/2; o15=(s1["o15"]+s2["o15"])/2; o25=(s1["o25"]+s2["o25"])/2; gg=(s1["gg"]+s2["gg"])/2
    best=None; best_perc=0
    if o05>=90 and o05>best_perc: best=f"Over 0.5 @ {o05:.0f}%"; best_perc=o05
    if o15>=90 and o15>best_perc: best=f"Over 1.5 @ {o15:.0f}%"; best_perc=o15
    if o25>=90 and o25>best_perc: best=f"Over 2.5 @ {o25:.0f}%"; best_perc=o25
    if gg>=90 and gg>best_perc: best=f"Gol @ {gg:.0f}%"; best_perc=gg
    return best
  except: return None
def run_bolla(cid=None,auto=False):
 try:
  tg("BOLLA MISTA 90% - Analizzo ultime 10 da adesso a mezzanotte...",cid,True)
  today=datetime.now(ROME).strftime("%Y-%m-%d")
  tomorrow=(datetime.now(ROME)+timedelta(days=1)).strftime("%Y-%m-%d")
  data=api(f"https://v3.football.api-sports.io/fixtures?date={today}") or []
  if data=="LIMIT": data=[]
  now_dt=datetime.now(ROME)
  sel=[]; checked=0
  for f in data:
   country=f.get("league",{}).get("country")
   if country not in TOP_LEAGUES: continue
   if f.get("league",{}).get("id")!=TOP_LEAGUES.get(country): continue
   if is_youth_league(f.get("league",{}).get("name","")): continue
   if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
   try: f_dt=datetime.fromisoformat(f.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
   except: continue
   if f_dt < now_dt: continue
   checked+=1
   if checked>25: break
   home_id=f.get("teams",{}).get("home",{}).get("id"); away_id=f.get("teams",{}).get("away",{}).get("id")
   best=get_best_stat_90(home_id,away_id)
   if best=="LIMIT": time.sleep(65); best=get_best_stat_90(home_id,away_id)
   if not best or best=="LIMIT": continue
   ora=f_dt.strftime("%H:%M"); league_name=f.get("league",{}).get("name",""); home=f.get("teams",{}).get("home",{}).get("name"); away=f.get("teams",{}).get("away",{}).get("name")
   sel.append(f"{ora} [{country} - {league_name}] {home} vs {away} -> {best}")
   if len(sel)>=33: break
  if not sel:
    data2=api(f"https://v3.football.api-sports.io/fixtures?date={tomorrow}") or []
    if data2!="LIMIT":
      for f in data2:
        country=f.get("league",{}).get("country")
        if country not in TOP_LEAGUES: continue
        if f.get("league",{}).get("id")!=TOP_LEAGUES.get(country): continue
        if is_youth_league(f.get("league",{}).get("name","")): continue
        if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
        home_id=f.get("teams",{}).get("home",{}).get("id"); away_id=f.get("teams",{}).get("away",{}).get("id")
        best=get_best_stat_90(home_id,away_id)
        if not best or best=="LIMIT": continue
        try: f_dt=datetime.fromisoformat(f.get("fixture",{}).get("date","").replace("Z","+00:00")).astimezone(ROME)
        except: continue
        ora=f_dt.strftime("%d %H:%M"); league_name=f.get("league",{}).get("name",""); home=f.get("teams",{}).get("home",{}).get("name"); away=f.get("teams",{}).get("away",{}).get("name")
        sel.append(f"{ora} [{country} - {league_name}] {home} vs {away} -> {best}")
        if len(sel)>=15: break
      if sel:
        out_txt=f"BOLLA MISTA 90% DOMANI - {len(sel)} partite (oggi finite, ti do domani)\n\n"
        for i,m in enumerate(sel,1): out_txt+=f"{i}. {m}\n"
        tg(out_txt,cid,True); return
  if sel:
   out_txt=f"BOLLA MISTA 90% - {len(sel)} partite odierne (90% ultime 10)\n\n"
   for i,m in enumerate(sel,1): out_txt+=f"{i}. {m}\n"
   tg(out_txt,cid,True)
  else:
   tg(f"0 partite 90% trovate. Controllate {checked} odierne. Domani mattina alle 9 ne trova 20-30.",cid,True)
 except Exception as e: tg(f"Errore bolla: {e}",cid,True)
def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=="LIMIT": return
    out=[]
    if not auto: tg("Cerco OVER 1.5...",cid,True)
    for f in data:
        try:
            country=f.get("league",{}).get("country")
            if country not in TOP_LEAGUES: continue
            if is_youth_league(f.get("league",{}).get("name","")): continue
            if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
            if f.get("league",{}).get("id")!=TOP_LEAGUES.get(country): continue
            fid=f.get("fixture",{}).get("id")
            over_odd=get_over_15(fid)
            if over_odd is None or over_odd>1.55: continue
            ora=str(f.get("fixture",{}).get("date",""))[11:16]
            league_name=f.get("league",{}).get("name",""); home=f.get("teams",{}).get("home",{}).get("name"); away=f.get("teams",{}).get("away",{}).get("name")
            out.append(f"{ora} [{country} - {league_name}] {home} vs {away} OVER 1.5 @ {over_odd}")
            time.sleep(0.4)
            if len(out)>=15: break
        except: continue
    if out:
        out_txt="DOPPIA "+str(len(out))+" OVER 1.5 CON NAZIONI\n\n"
        for i,m in enumerate(out,1): out_txt+=f"{i}. {m}\n"
        tg(out_txt,cid,True)
    else:
        if not auto: tg("Oggi nessun OVER 1.5",cid,True)
def poll():
 global is_paused,last_id
 try:
  if BOT: requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
 except: pass
 while True:
  try:
   if not BOT: time.sleep(60); continue
   base="https://api.telegram.org/bot"+BOT
   url=base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     msg=u.get("message",{}); txt=(msg.get("text") or "").strip(); low=txt.lower(); cid=msg.get("chat",{}).get("id")
     if not txt: continue
     if "chiudi menu" in low: tg("Menu chiuso",cid,True,True); continue
     elif "apri menu" in low: tg("Menu aperto V54 NAZIONI",cid,True,False); continue
     elif "spegni" in low: is_paused=True; tg("PAUSA",cid,True); continue
     elif "accendi" in low or "/start" in low: is_paused=False; tg("V54 ATTIVO CON NAZIONI",cid,True); continue
     elif "status" in low: tg("STATUS V54 OK CON NAZIONI",cid,True); continue
     elif "doppia" in low: run_doppia(cid); continue
     elif "bolla" in low: run_bolla(cid); continue
  except: pass
  time.sleep(2)
def live_loop():
 tg("BOT V54 ATTIVO - CON NAZIONI",None,True)
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
    home=g.get("teams",{}).get("home",{}).get("name"); away=g.get("teams",{}).get("away",{}).get("name")
    gh=g.get("goals",{}).get("home"); ga=g.get("goals",{}).get("away")
    country=g.get("league",{}).get("country",""); league_name=g.get("league",{}).get("name","")
    label=f"[{country} - {league_name}]"
    if fid not in av_sfiga_score: av_sfiga_score[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga_score[fid]
     if gh!=oh or ga!=oa:
      chi="HOME" if gh>oh else "AWAY"; av_sfiga_score[fid]=(gh,ga)
      sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       if chi==tipo:
        sfiga_gol = gh if tipo=="HOME" else ga; fav_gol = ga if tipo=="HOME" else gh
        if sfiga_gol >= fav_gol:
            stato="PAREGGIA" if sfiga_gol==fav_gol else "VANTAGGIO"
            ns=home if tipo=="HOME" else away; nf=away if tipo=="HOME" else home
            full=f"SFIGATA {stato} {mm}' {label} {home} {gh}-{ga} {away}\nSfigata {ns} @{qs}\nFavorita {nf} @{qf}"
            tg(full)
    if 30<=mm<=45 and fid not in av_s_first:
     u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid); st=api(u); sot=0; corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s.get("statistics",[]):
        t=x.get("type","")
        if "Shots on Goal" in t:
         try: sot+=int(str(x.get("value") or 0))
         except: pass
        if "corner" in t.lower():
         try: corn+=int(str(x.get("value") or 0))
         except: pass
     if sot>=4 or corn>=6:
        tg(f"PREPARATI {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot}"); av_s_first.add(fid)
    if 65<=mm<=90 and fid not in av_s:
     u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid); st=api(u); sot=0; corn=0
     if st and len(st)>=2:
      for s in st:
       for x in s.get("statistics",[]):
        t=x.get("type","")
        if "Shots on Goal" in t:
         try: sot+=int(str(x.get("value") or 0))
         except: pass
        if "corner" in t.lower():
         try: corn+=int(str(x.get("value") or 0))
         except: pass
     if sot>=4 or corn>=6:
        tg(f"GIOCALO {mm}' {label} {home} {gh}-{ga} {away} Tiri:{sot} Corner:{corn}"); av_s.add(fid); av_g[fid]=gh+ga
   for g in games:
    fid=g.get("fixture",{}).get("id")
    if fid in av_g:
     gh2=g.get("goals",{}).get("home"); ga2=g.get("goals",{}).get("away")
     if gh2+ga2>av_g[fid]:
         country=g.get("league",{}).get("country",""); league_name=g.get("league",{}).get("name","")
         label=f"[{country} - {league_name}]"
         hn=g.get("teams",{}).get("home",{}).get("name"); an=g.get("teams",{}).get("away",{}).get("name")
         tg(f"GOAL VINTO! {label} {hn} {gh2}-{ga2} {an}"); del av_g[fid]
   time.sleep(60)
  except Exception as e: print(e); time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
