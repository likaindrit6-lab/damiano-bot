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
        if x in n:
            return True
    return False

app=Flask(__name__)

@app.route("/")
def home():
    return f"BOT V43 OK - {datetime.now(ITALY).strftime('%H:%M')}",200

TAST=json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["\U0001f4ca STATISTICHE 35 NAZIONI"],["\U0001f6a9 CALCIO D'ANGOLO +6"],["STATUS"],["ACCENDI","SPEGNI"],["\u274c CHIUDI MENU"]],"resize_keyboard":True,"is_persistent":False})
TAST_CHIUSA=json.dumps({"keyboard":[["\U0001f3ae APRI MENU"]],"resize_keyboard":True,"is_persistent":False})

def tg(m,cid=None,keys=False,chiusa=False,home=None,away=None):
 try:
  cid=cid or CHAT
  if not cid or not BOT:
      return
  base="https://api.telegram.org/bot"+BOT
  if home and away:
      q=urllib.parse.quote_plus(home+" "+away)
      q2=urllib.parse.quote_plus(home+" "+away+" quote live")
      inline_kb={"inline_keyboard":[[{"text":"\U0001f4ca LIVE SOFASCORE","url":"https://www.sofascore.com/search?q="+q},{"text":"\U0001f50d QUOTE LIVE","url":"https://www.google.com/search?q="+q2}]]}
      pay={"chat_id":cid,"text":m,"parse_mode":"HTML","reply_markup":inline_kb}
  else:
      pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
      if keys:
          if chiusa:
              pay["reply_markup"]=json.loads(TAST_CHIUSA)
          else:
              pay["reply_markup"]=json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=25)
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

def get_corners_fixture(fid):
 try:
  u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid)
  stats=api(u)
  if not stats or stats=="LIMIT" or len(stats)<2:
      return None
  tot=0
  found=False
  for team in stats:
   for s in team.get("statistics",[]):
    stype=str(s.get("type","")).lower()
    if "corner" in stype:
     try:
      tot+=int(str(s.get("value") or 0))
      found=True
     except:
      pass
  if found:
      return tot
  return None
 except:
  return None

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

def media_tutte_35(cid):
    tg("\u23f3 PARTITO STATISTICHE 35 NAZIONI - 4 min",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            u="https://v3.football.api-sports.io/teams?league="+str(lid)+"&season=2024"
            teams=api(u)
            if not teams or teams=="LIMIT":
                continue
            txt=country.upper()+" - "+datetime.now(ITALY).strftime("%d/%m %H:%M")+"\n\n"
            for t in teams[:14]:
              tid=t.get("team",{}).get("id")
              tname=t.get("team",{}).get("name")
              uu="https://v3.football.api-sports.io/fixtures?team="+str(tid)+"&last=10&season=2024"
              last=api(uu)
              if not last or last=="LIMIT":
                  time.sleep(0.4)
                  continue
              tot=0
              c=0
              for p in last:
               gh=p.get("goals",{}).get("home")
               if gh is None:
                   continue
               ga=p.get("goals",{}).get("away")
               tot+=gh+ga
               c+=1
              if c==0:
                  continue
              med=tot/c
              if med>2:
                  txt+="PIU DI 2 - "+tname+": "+str(round(med,2))+"\n"
              else:
                  txt+="MENO DI 2 - "+tname+": "+str(round(med,2))+"\n"
              time.sleep(0.3)
            tg(txt,cid,True)
            time.sleep(1)
        except:
            pass
    tg("\u2705 FINITO STATISTICHE 35 GOL",cid,True)

def media_tutte_angoli(cid):
    tg("\u23f3 PARTITO CALCIO D'ANGOLO +6 - 35 NAZIONI",cid,True)
    for country, lid in TOP_LEAGUES.items():
        try:
            u="https://v3.football.api-sports.io/teams?league="+str(lid)+"&season=2025"
            teams=api(u)
            if not teams or teams=="LIMIT":
              uu="https://v3.football.api-sports.io/teams?league="+str(lid)+"&season=2024"
              teams=api(uu)
            if not teams or teams=="LIMIT":
                continue
            txt="\U0001f6a9 "+country.upper()+" - CORNER\n\n"
            trovati=0
            for t in teams[:14]:
              tid=t.get("team",{}).get("id")
              tname=t.get("team",{}).get("name")
              uu="https://v3.football.api-sports.io/fixtures?team="+str(tid)+"&last=10"
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
               txt+="\U0001f525 "+tname+": "+str(round(med,1))+" corner\n"
               trovati+=1
              time.sleep(0.3)
            if trovati==0:
              txt+="Nessuna squadra con +6 corner in "+country+"\n"
            tg(txt,cid,True)
            time.sleep(1)
        except Exception as e:
            tg("Errore "+country+": "+str(e),cid,True)
    tg("\u2705 FINITO ANGOLI +6",cid,True)

def get_double_chance(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
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
          return "1X @ "+str(best_odd)
      if "Draw/Away" in best:
          return "X2 @ "+str(best_odd)
      if "Home/Away" in best:
          return "12 @ "+str(best_odd)
 except:
  pass
 return None

def get_over_15(fid):
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
           continue
 except:
  pass
 return None

def get_fixtures_today():
 today=datetime.now(ROME).strftime("%Y-%m-%d")
 u="https://v3.football.api-sports.io/fixtures?date="+today
 return api(u)

def run_bolla(cid=None,auto=False):
 data=get_fixtures_today()
 if not data or data=="LIMIT":
  if not auto:
      tg("BOLLA: Limite API",cid,True)
  return
 sel=[]
 if not auto:
     tg("Cerco TOP LEAGUE + DOPPIA...",cid,True)
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
  ora=str(found.get("fixture",{}).get("date",""))[11:16]
  home=found.get("teams",{}).get("home",{}).get("name")
  away=found.get("teams",{}).get("away",{}).get("name")
  league=found.get("league",{}).get("name")
  dc=get_double_chance(fid) or "1X"
  sel.append(ora+" "+home+" vs "+away+" -> "+dc+" ("+league+")")
  if len(sel)>=35:
      break
 if not sel:
  if not auto:
      tg("Oggi nessuna TOP LEAGUE in programma",cid,True)
  return
 out_txt="BOLLA EUROPA "+str(len(sel))+" NAZIONI\n\n"
 num=1
 for m in sel:
     out_txt+=str(num)+". "+m+"\n"
     num+=1
 tg(out_txt,cid,True)

def run_doppia(cid=None,auto=False):
    data=get_fixtures_today()
    if not data or data=="LIMIT":
        return
    out=[]
    if not auto:
        tg("Cerco OVER 1.5...",cid,True)
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
            ora=str(f.get("fixture",{}).get("date",""))[11:16]
            home=f.get("teams",{}).get("home",{}).get("name")
            away=f.get("teams",{}).get("away",{}).get("name")
            league=f.get("league",{}).get("name")
            out.append(ora+" "+home+" vs "+away+" -> OVER 1.5 @ "+str(over_odd)+" ("+league+")")
            time.sleep(0.4)
            if len(out)>=15:
                break
        except:
            continue
    if out:
        out_txt="DOPPIA "+str(len(out))+" OVER 1.5\n\n"
        num=1
        for m in out:
            out_txt+=str(num)+". "+m+"\n"
            num+=1
        tg(out_txt,cid,True)
    else:
        if not auto:
            tg("Oggi nessun OVER 1.5 <1.55",cid,True)

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
       time.sleep(60)
       continue
   base="https://api.telegram.org/bot"+BOT
   url=base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20"
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
         tg("\u2705 Menu chiuso",cid,True,True)
         continue
     elif "apri menu" in low:
         tg("\u2705 Menu aperto V43",cid,True,False)
         continue
     elif "spegni" in low:
         is_paused=True
         tg("\u23f8\ufe0f PAUSA",cid,True)
         continue
     elif "accendi" in low or "/start" in low:
         is_paused=False
         tg("\u25b6\ufe0f V43 ATTIVO - FIX TOTALE + BOTTONI",cid,True)
         continue
     elif "angolo" in low or "calcio d" in low:
         threading.Thread(target=media_tutte_angoli,args=(cid,),daemon=True).start()
         continue
     elif "statistiche 35" in low:
         threading.Thread(target=media_tutte_35,args=(cid,),daemon=True).start()
         continue
     elif "status" in low:
         tg("STATUS V43 - "+datetime.now(ITALY).strftime("%H:%M"),cid,True)
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
 tg("\u2705 BOT V43 ATTIVO\n\U0001f4ca FILTRO 1T >=4\n\u26bd SFIGATA SOLO PAREGGIO/VANTAGGIO\n\U0001f517 BOTTONI OK",None,True)
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
            if sfiga_gol == fav_gol:
                stato="PAREGGIA"
            else:
                stato="VA IN VANTAGGIO"
            txt="\u26bd SFIGATA "+stato+" "+str(m)+"' "+co+" "+home+" "+str(gh)+"-"+str(
