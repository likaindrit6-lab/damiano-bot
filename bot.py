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
    return any(x in n for x in bad)

app=Flask(__name__)
@app.route("/")
def home():
    return f"BOT V42 FIX FINALE - {datetime.now(ITALY).strftime('%H:%M')}",200

TAST=json.dumps({"keyboard":[
["Serie A","Serie B","Inghilterra"],
["Spagna","Germania","Francia"],
["Olanda","Portogallo","Turchia"],
["DOPPIA ALTA %"],
["BOLLA EUROPA 33 NAZIONI"],
["📊 STATISTICHE 35 NAZIONI"],
["🚩 CALCIO D'ANGOLO +6"],
["STATUS"],
["ACCENDI","SPEGNI"],
["❌ CHIUDI MENU"]
],"resize_keyboard":True,"is_persistent":False})

TAST_CHIUSA=json.dumps({"keyboard":[["\U0001f3ae APRI MENU"]],"resize_keyboard":True,"is_persistent":False})

def tg(m,cid=None,keys=False,chiusa=False,home=None,away=None):
 try:
  cid=cid or CHAT
  if not cid or not BOT:
      return
  base=f"https://api.telegram.org/bot{BOT}"
  if home and away:
      q = urllib.parse.quote_plus(f"{home} {away}")
      q2 = urllib.parse.quote_plus(f"{home} {away} quote live")
      inline_kb = {
          "inline_keyboard": [
              [
                  {"text": "📊 LIVE SOFASCORE", "url": f"https://www.sofascore.com/search?q={q}"},
                  {"text": "🔍 QUOTE LIVE", "url": f"https://www.google.com/search?q={q2}"}
              ]
          ]
      }
      pay={"chat_id":cid,"text":m,"parse_mode":"HTML","reply_markup":inline_kb}
  else:
      pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
      if keys:
          pay["reply_markup"]=json.loads(TAST_CHIUSA if chiusa else TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=25)
 except Exception as e:
  print(f"tg error {e}")

def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429:
      return "LIMIT"
  return r.json().get("response",[])
 except:
  return []

def get_corners_fixture(fid):
 try:
  u=f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}"
  stats=api(u)
  if not stats or stats=="LIMIT" or len(stats)<2:
      return None
  tot=0
  found=False
  for team in stats:
   for s in team.get("statistics",[]):
    if "corner" in str(s.get("type","")).lower():
     try:
      tot+=int(str(s.get("value") or 0))
      found=True
     except:
      pass
  return tot if found else None
 except:
  return None

def get_sfigata(fid):
 try:
  u=f"https://v3.football.api-sports.io/odds?fixture={fid}"
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

def media(league_id,name):
 txt=f"{name.upper()} - {datetime.now(ITALY).strftime('%d/%m %H:%M')}\n\n"
 u=f"https://v3.football.api-sports.io/teams?league={league_id}&season=2024"
 teams=api(u)
 if not teams or teams=="LIMIT":
     return f"Errore API {name}"
 for t in teams[:14]:
  tid=t.get("team",{}).get("id")
  tname=t.get("team",{}).get("name")
  uu=f"https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024"
  last=api(uu)
  if not last or last=="LIMIT":
      time.sleep(0.4)
      continue
  tot=0
  c=0
  for p in last:
   gh=p.get("goals",{}).get("home")
   ga=p.get("goals",{}).get("away")
   if gh is None:
       continue
   tot+=gh+ga
   c+=1
  if c==0:
      continue
  med=tot/c
  txt+=("PIU DI 2" if med>2 else "MENO DI 2")+f" - {tname}: {med:.2f}\n"
  time.sleep(0.3)
 return txt

def media_tutte_35(cid):
    tg("⏳ PARTITO STATISTICHE 35 NAZIONI - 4 min",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            res=media(lid, country)
            tg(res,cid,True)
            time.sleep(1)
        except:
            pass
    tg("✅ FINITO STATISTICHE 35 GOL",cid,True)

def media_angoli(league_id,name):
 txt=f"🚩 {name.upper()} - CORNER MEDIA ULTIME 10\n{datetime.now(ITALY).strftime('%d/%m')}\n\n"
 u=f"https://v3.football.api-sports.io/teams?league={league_id}&season=2025"
 teams=api(u)
 if not teams or teams=="LIMIT":
  uu=f"https://v3.football.api-sports.io/teams?league={league_id}&season=2024"
  teams=api(uu)
 if not teams or teams=="LIMIT":
     return f"Errore API {name}"
 trovati=0
 for t in teams[:14]:
  tid=t.get("team",{}).get("id")
  tname=t.get("team",{}).get("name")
  uu=f"https://v3.football.api-sports.io/fixtures?team={tid}&last=10"
  last=api(uu)
  if not last or last=="LIMIT":
      time.sleep(0.4)
      continue
  tot_corners=0
  c=0
  for p in last:
   if p.get("fixture",{}).get("status",{}).get("short")!="FT":
       continue
   fid=p.get("fixture",{}).get("id")
   corn=get_corners_fixture(fid)
   if corn is None:
       continue
   tot_corners+=corn
   c+=1
   time.sleep(0.35)
  if c==0:
      continue
  med=tot_corners/c
  if med>=6.0:
   txt+=f"🔥 {tname}: {med:.1f} corner ({c} partite)\n"
   trovati+=1
  time.sleep(0.3)
 if trovati==0:
  txt+=f"Nessuna squadra con +6 corner in {name}\nMedia più bassa di 6"
 return txt

def media_tutte_angoli(cid):
    tg("⏳ PARTITO CALCIO D'ANGOLO +6 - 35 NAZIONI\nCi metto 8-10 minuti\nFiltro solo >6 corner/partita",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            res=media_angoli(lid, country)
            tg(res,cid,True)
            time.sleep(1)
        except Exception as e:
            tg(f"Errore {country}: {e}",cid,True)
    tg("✅ FINITO ANGOLI +6",cid,True)

def get_double_chance(fid):
 try:
  u=f"https://v3.football.api-sports.io/odds?fixture={fid}"
  data=api(u)
  if not data or data=="LIMIT":
      return None
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    if "Double Chance" in bet.get("name",""):
     best=None
     best_odd=10
     for v in bet.get("values",[]):
      try:
       odd=float(v.get("odd"))
       if odd<best_odd:
           best_odd=odd
           best=v.get("value")
      except:
       continue
     if best:
      if "Home/Draw" in best:
          return f"1X @ {best_odd}"
      if "Draw/Away" in best:
          return f"X2 @ {best_odd}"
      if "Home/Away" in best:
          return f"12 @ {best_odd}"
 except:
  pass
 return None

def get_over_15(fid):
 try:
  u=f"https://v3.football.api-sports.io/odds?fixture={fid}"
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
           continue
 except:
  pass
 return None

def get_fixtures_today():
 today=datetime.now(ROME).strftime("%Y-%m-%d")
 u=f"https://v3.football.api-sports.io/fixtures?date={today}"
 return api(u)

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=="LIMIT":
  if not auto:
      tg("BOLLA: Limite API",cid,True)
  return
 sel=[]
 if not auto:
     tg("⏳ Cerco TOP LEAGUE + DOPPIA...",cid,True)
 for country,top_id in TOP_LEAGUES.items():
  found=None
  for f in data:
   if f.get("league",{}).get("id")==top_id and f.get("league",{}).get("country")==country:
    if is_youth_league(f.get("league",{}).get("name","")):
        continue
    if f.get("fixture",{}).get("status",{}).get("short")!="NS":
        continue
    found=f
    break
  if not found:
      continue
  fid=found.get("fixture",{}).get("id")
  ora=found.get("fixture",{}).get("date","")[11:16]
  home=found.get("teams",{}).get("home",{}).get("name")
  away=found.get("teams",{}).get("away",{}).get("name")
  league=found.get("league",{}).get("name")
  dc=get_double_chance(fid) or "1X"
  sel.append(f"{ora} {home} vs {away} -> {dc} ({league} - {country})")
  if len(sel)>=35:
      break
 if not sel:
  if not auto:
      tg("Oggi nessuna TOP LEAGUE in programma",cid,True)
  return
 tg(f"🌍 BOLLA EUROPA {len(sel)} NAZIONI\n\n" + "\n".join([f"{i+1}. {m}" for i,m in enumerate(sel)]),cid,True)

def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=="LIMIT":
        return
    out=[]
    if not auto:
        tg("⏳ Cerco OVER 1.5...",cid,True)
    for f in data:
        try:
            if f.get("league",{}).get("country") not in TOP_LEAGUES:
                continue
            if is_youth_league(f.get("league",{}).get("name","")):
                continue
            if f.get("fixture",{}).get("status",{}).get("short")!="NS":
                continue
            if f.get("league",{}).get("id")!=TOP_LEAGUES.get(f.get("league",{}).get("country")):
                continue
            fid=f.get("fixture",{}).get("id")
            over_odd=get_over_15(fid)
            if over_odd is None or over_odd>1.55:
                continue
            ora=f.get("fixture",{}).get("date","")[11:16]
            home=f.get("teams",{}).get("home",{}).get("name")
            away=f.get("teams",{}).get("away",{}).get("name")
            league=f.get("league",{}).get("name")
            out.append(f"{ora} {home} vs {away} -> OVER 1.5 @ {over_odd} ({league})")
            time.sleep(0.4)
            if len(out)>=15:
                break
        except:
            continue
    if out:
        tg(f"🔥 DOPPIA {len(out)} OVER 1.5\n\n" + "\n".join([f"{i+1}. {m}" for i,m in enumerate(out)]),cid,True)
    else:
        if not auto:
            tg("🔥 Oggi nessun OVER 1.5 <1.55",cid,True)

def poll():
 global is_paused,last_id
 try:
  if BOT:
      requests.get(f"https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true",timeout=10)
 except:
  pass
 while True:
  try:
   if not BOT:
       time.sleep(60)
       continue
   base=f"https://api.telegram.org/bot{BOT}"
   url=base+f"/getUpdates?offset={last_id+1}&timeout=20"
   r=requests.get(url,timeout=30).json()
   if r.get("ok"):
    for u in r.get("result",[]):
     last_id=u["update_id"]
     msg=u.get("message",{})
     txt=(msg.get("text") or "").strip()
     low=txt.lower()
     cid=msg.get("chat",{}).get("id")
     if not txt:
         continue
     if "chiudi menu" in low:
         tg("✅ Menu chiuso",cid,True,True)
         continue
     elif "apri menu" in low:
         tg("✅ Menu aperto V42",cid,True,False)
         continue
     elif "spegni" in low:
         is_paused=True
         tg("⏸️ PAUSA",cid,True)
         continue
     elif "accendi" in low or "/start" in low:
         is_paused=False
         tg("▶️ V42 ATTIVO - FIX FINALE + BOTTONI OK",cid,True)
         continue
     elif "angolo" in low or "calcio d" in low:
         threading.Thread(target=media_tutte_angoli,args=(cid,),daemon=True).start()
         continue
     elif "statistiche 35" in low:
         threading.Thread(target=media_tutte_35,args=(cid,),daemon=True).start()
         continue
     elif "status" in low:
         tg(f"STATUS V42 FIX - {datetime.now(ITALY).strftime('%H:%M')}",cid,True)
         continue
     elif "doppia" in low:
         run_doppia(cid)
         continue
     elif "bolla" in low:
         run_bolla(cid)
         continue
  except:
   pass
  time.sleep(2)

def live_loop():
 tg("✅ BOT V42 FIX FINALE ATTIVO\n📊 FILTRO 1T >=4\n⚽ SFIGATA SOLO PAREGGIO/VANTAGGIO\n🔗 BOTTONI OK",None,True)
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
    m=g.get("fixture",{}).get("status",{}).get("elapsed")
    if m is None:
        continue
    home=g.get("teams",{}).get("home",{}).get("name")
    away=g.get("teams",{}).get("away",{}).get("name")
    gh=g.get("goals",{}).get("home")
    ga=g.get("goals",{}).get("away")

    if fid not in av_sfiga_score:
     av_sfiga_score[fid]=(gh,ga)
    else:
     oh,oa=av_sfiga_score[fid]
     if gh!=oh or ga!=oa:
      chi="HOME" if gh>oh else "AWAY"
      av_sfiga_score[fid]=(gh,ga)
      sf=get_sfigata(fid)
      if sf:
       tipo,qs,tf,qf=sf
       if chi==tipo:
        sfiga_gol = gh if tipo=="HOME" else ga
        fav_gol = ga if tipo=="HOME" else gh
        if sfiga_gol >= fav_gol:
            ns=home if tipo=="HOME" else away
            nf=away if tipo=="HOME" else home
            co=g.get("league",{}).get("country")
            stato = "PAREGGIA" if sfiga_gol == fav_gol else "VA IN VANTAGGIO"
            txt=f"⚽ SFIGATA {stato} {m}' {co} {home} {gh}-{ga} {away}\n"
            txt+=f"Sfigata {ns} @{qs} {stato.lower()}!\n"
            txt+=f"Favorita {nf} @{qf} in difficoltà\n"
            txt+=f"👉 RIGIOCA SUBITO GOL FAV / OVER"
            tg(txt, home=home, away=away)

    if 30<=m<=45 and fid not in av_s_first:
     u=f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}"
     st=api(u)
     sot=0
     corn=0
     if st and len(st)>=2:
      for s in st:
       for x in
