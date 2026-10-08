import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
try:
 base="https://api.telegram.org/bot"+BOT_TOKEN
 requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass
app=Flask(__name__)
@app.route('/')
def home():
 s="PAUSA" if is_paused else "ATTIVO"
 return "BOT V30.9 CLEAN - "+s,200
def run_flask():
 from waitress import serve
 p=int(os.environ.get("PORT",10000))
 serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()
TASTIERA_JSON=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BLASONATE LUN-SAB","PARTITE OGGI"],["UNDER","TOKEN"]],"resize_keyboard":True,"is_persistent":True})
def tg(m,chat_id=None,con_tastiera=False):
 try:
  cid=chat_id if chat_id else CHAT_ID
  url="https://api.telegram.org/bot"+BOT_TOKEN+"/sendMessage"
  payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
  if con_tastiera: payload["reply_markup"]=TASTIERA_JSON
  if len(m)>3900:
   for i in range(0,len(m),3900):
    payload["text"]=m[i:i+3900]
    if i>0: payload.pop("reply_markup",None)
    requests.post(url,json=payload,timeout=25)
    time.sleep(0.5)
  else: requests.post(url,json=payload,timeout=25)
 except: pass
def api_get(url):
 if is_paused: return []
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []
def get_token_status():
 try:
  r=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10)
  d=r.json()["response"]["requests"]
  return "TOKEN %s/%s Rimasti:%s" % (d['current'],d['limit_day'],d['limit_day']-d['current'])
 except Exception as e: return "Errore token: "+str(e)
def get_flag(p):
 m={"Italy":"IT","England":"GB","Spain":"ES","Germany":"DE","France":"FR","Portugal":"PT","Netherlands":"NL","Belgium":"BE","Turkey":"TR","Brazil":"BR","Argentina":"AR"}
 return m.get(p,"")
def is_ok_league(l,c):
 s=(l+" "+c).lower()
 bad=["women","female","u19","u21","u23","u20","reserve","youth","futsal","amateur"]
 for x in bad:
  if x in s: return False
 return True
def is_team_ok(home,away):
 t=(home+" "+away).lower()
 if " ii" in t: return False
 if home.endswith(" II"): return False
 if away.endswith(" II"): return False
 return True
def is_blasonata(l,c):
 if not is_ok_league(l,c): return False
 allowed=["Italy","England","Spain","Germany","France","Portugal","Netherlands","Belgium","Brazil","Argentina"]
 if c not in allowed: return False
 ln=l.lower()
 keys=["serie a","serie b","premier league","championship","la liga","laliga","segunda","bundesliga","ligue 1","ligue 2","primeira","eredivisie","pro league","brasileiro","liga profesional"]
 for k in keys:
  if k in ln: return True
 return False
def get_lun_sab():
 oggi=datetime.now(ITALY)
 lun=oggi-timedelta(days=oggi.weekday())
 sab=lun+timedelta(days=5)
 return lun,sab
def crea_blasonate_lun_sab():
 try:
  d1,d2=get_lun_sab()
  label=d1.strftime("%d/%m")+"->"+d2.strftime("%d/%m")
  tutte=[]
  for i in range((d2-d1).days+1):
   giorno=(d1+timedelta(days=i)).strftime("%Y-%m-%d")
   fx=api_get("https://v3.football.api-sports.io/fixtures?date="+giorno)
   if fx=="LIMIT": continue
   fx=[f for f in fx if is_blasonata(f['league']['name'],f['league']['country'])]
   fx=[f for f in fx if is_team_ok(f['teams']['home']['name'],f['teams']['away']['name'])]
   tutte.extend(fx)
   time.sleep(0.2)
  if not tutte: return "Sosta - 0 blasonate "+label
  cand=[]
  no_odds=0
  for p in sorted(tutte,key=lambda x:x["fixture"]["timestamp"]):
   if len(cand)>=80: break
   fid=p["fixture"]["id"]
   dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
   home=p['teams']['home']['name']
   away=p['teams']['away']['name']
   paese=p['league']['country']
   lega=p['league']['name']
   flag=get_flag(paese)
   ora=dt.strftime("%d/%m %H:%M")
   odds=api_get("https://v3.football.api-sports.io/odds?fixture="+str(fid))
   if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"):
    no_odds+=1
    continue
   best=None
   for b in odds[0]["bookmakers"]:
    for bet in b["bets"]:
     bn=bet["name"].lower()
     if "double chance" in bn or "multigoal" in bn:
      for v in bet["values"]:
       try:
        q=float(v["odd"])
        if 1.08 <= q <= 1.55:
         if not best or q < best["q"]:
          best={"q":q,"m":bet["name"],"e":v["value"]}
       except: pass
   if not best:
    no_odds+=1
    continue
   qenc=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
   link="https://www.google.com/search?q="+qenc+"&btnI=1"
   prob=int((1/best["q"])*100)
   if "Double" in best["m"]: tipo="DOPPIA "+best["e"].replace("Home/Draw","1X").replace("Draw/Away","X2")
   else: tipo="MULTIGOL "+best["e"]
   txt="%s %s | %s | %s\n%s vs %s\n-> %s @ %s (%s%%)\n%s" % (flag,paese.upper(),ora,lega,home,away,tipo,str(best["q"]),prob,link)
   cand.append({"q":best["q"],"txt":txt})
  if not cand:
   msg="0 blasonate con quota - saltate senza quote: "+str(no_odds)
   return msg
  cand=sorted(cand,key=lambda x:x["q"])
  picks=cand[:25]
  tot=1
  for x in picks: tot*=x["q"]
  body="\n\n".join([p["txt"] for p in picks])
  return "BLASONATE LUN-SAB %s - %s PARTITE - Quota %.2f\n\n%s\n\nTOT %.2f - Senza quota: %s" % (label,len(picks),tot,body,tot,no_odds)
 except Exception as e: return "Errore blasonate: "+str(e)
def crea_partite_oggi():
 try:
  OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
  fx=api_get("https://v3.football.api-sports.io/fixtures?date="+OGGI)
  if fx=="LIMIT": return "Limite API"
  fx=[f for f in fx if is_ok_league(f['league']['name'],f['league']['country'])]
  fx=[f for f in fx if is_team_ok(f['teams']['home']['name'],f['teams']['away']['name'])]
  cand=[]
  for p in fx:
   if len(cand)>=100: break
   fid=p["fixture"]["id"]
   dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
   if dt < datetime.now(ITALY): continue
   home=p['teams']['home']['name']
   away=p['teams']['away']['name']
   paese=p['league']['country']
   lega=p['league']['name']
   flag=get_flag(paese)
   ora=dt.strftime("%H:%M")
   odds=api_get("https://v3.football.api-sports.io/odds?fixture="+str(fid))
   if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
   best=None
   for b in odds[0]["bookmakers"]:
    for bet in b["bets"]:
     bn=bet["name"].lower()
     if "double chance" in bn or "multigoal" in bn:
      for v in bet["values"]:
       try:
        q=float(v["odd"])
        if 1.08 <= q <= 1.35:
         if not best or q < best["q"]: best={"q":q,"m":bet["name"],"e":v["value"]}
       except: pass
   if not best: continue
   qenc=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
   link="https://www.google.com/search?q="+qenc+"&btnI=1"
   prob=int((1/best["q"])*100)
   tipo="DOPPIA "+best["e"] if "Double" in best["m"] else "MULTIGOL "+best["e"]
   txt="%s %s | %s | %s\n%s vs %s\n-> %s @ %s (%s%%)\n%s" % (flag,paese.upper(),ora,lega,home,away,tipo,str(best["q"]),prob,link)
   cand.append({"q":best["q"],"txt":txt})
  if not cand: return "0 partite oggi"
  cand=sorted(cand,key=lambda x:x["q"])
  picks=cand[:15]
  tot=1
  for x in picks: tot*=x["q"]
  body="\n\n".join([p["txt"] for p in picks])
  return "PARTITE OGGI %s - %s partite - %.2f\n\n%s" % (OGGI,len(picks),tot,body)
 except Exception as e: return "Errore oggi: "+str(e)
def crea_under():
 try:
  OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
  fx=api_get("https://v3.football.api-sports.io/fixtures?date="+OGGI)
  fx=[f for f in fx if is_ok_league(f['league']['name'],f['league']['country'])]
  picks=[]
  for p in fx:
   if len(picks)>=10: break
   fid=p["fixture"]["id"]
   dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
   if dt < datetime.now(ITALY): continue
   home=p['teams']['home']['name']
   away=p['teams']['away']['name']
   paese=p['league']['country']
   lega=p['league']['name']
   flag=get_flag(paese)
   ora=dt.strftime("%H:%M")
   odds=api_get("https://v3.football.api-sports.io/odds?fixture="+str(fid))
   if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
   for b in odds[0]["bookmakers"]:
    for bet in b["bets"]:
     if "Over/Under" in bet["name"]:
      for v in bet["values"]:
       if "Under 4.5" in v["value"]:
        try:
         q=float(v["odd"])
         if 1.12 <= q <= 1.40:
          qenc=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
          link="https://www.google.com/search?q="+qenc+"&btnI=1"
          prob=int((1/q)*100)
          txt="%s %s | %s | %s\n%s vs %s\n-> UNDER 4.5 @ %s (%s%%)\n%s" % (flag,paese.upper(),ora,lega,home,away,str(q),prob,link)
          picks.append(txt)
        except: pass
  if not picks: return "0 UNDER oggi"
  body="\n\n".join(picks)
  return "UNDER 4.5 OGGI - %s partite\n\n%s" % (len(picks),body)
 except Exception as e: return "Errore under: "+str(e)
def poll_commands():
 global is_paused,last_update_id
 while True:
  try:
   base="https://api.telegram.org/bot"+BOT_TOKEN
   r=requests.get(base+"/getUpdates?offset="+str(last_update_id+1)+"&timeout=25",timeout=35).json()
   if r.get("ok"):
    for upd in r.get("result",[]):
     last_update_id=upd["update_id"]
     txt=upd.get("message",{}).get("text","").lower()
     chat=upd.get("message",{}).get("chat",{}).get("id")
     if "spegni" in txt:
      is_paused=True
      tg("PAUSA 0 CONSUMI",chat,con_tastiera=True)
     elif "accendi" in txt or "/start" in txt:
      is_paused=False
      tg("BOT V30.9 PRONTO - FIXATO",chat,con_tastiera=True)
     elif "token" in txt: tg(get_token_status(),chat,con_tastiera=True)
     elif "lun-sab" in txt:
      tg("Cerco BLASONATE LUN-SAB 20-25...",chat)
      tg(crea_blasonate_lun_sab(),chat,con_tastiera=True)
     elif "partite oggi" in txt:
      tg("Cerco PARTITE OGGI...",chat)
      tg(crea_partite_oggi(),chat,con_tastiera=True)
     elif "under" in txt:
      tg("Cerco UNDER...",chat)
      tg(crea_under(),chat,con_tastiera=True)
  except: pass
  time.sleep(2)
threading.Thread(target=poll_commands,daemon=True).start()
while True:
 try:
  if is_paused:
   time.sleep(300)
   continue
  now=datetime.now(ITALY)
  if 0 <= now.hour < 10:
   time.sleep(600)
   continue
  time.sleep(180)
 except: time.sleep(15)
