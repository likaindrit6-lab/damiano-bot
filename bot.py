import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta
print("AVVIO BOT V13.7 FINAL COMPLETO")
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_update_id=0;av_g={};av_s=set();pre=set();pre1=set();cache={};tripla_coda=[];ultimo_invio_tripla=time.time()
try:
 requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass
app=Flask(__name__)
@app.route('/')
def home():
 stato="PAUSA" if is_paused else "ATTIVO"
 return f"BOT V13.7 FINAL - {stato}",200
def run_flask():
 from waitress import serve
 serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()
TASTIERA_JSON=json.dumps({"keyboard":[["ACCONDI","SPEGNI"],["BOLLA","STATUS"]],"resize_keyboard":True,"is_persistent":True})
def tg(m,chat_id=None,con_tastiera=False):
 try:
  cid=chat_id if chat_id else CHAT_ID
  payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
  if con_tastiera: payload["reply_markup"]=TASTIERA_JSON
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json=payload,timeout=25)
 except: pass
def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []
def get_stat(arr,name):
 for s in arr:
  if s.get('type')==name:
   try:
    v=str(s.get('value') or 0).replace('%','').strip()
    return int(v or 0)
   except: return 0
 return 0
def get_flag(p): return p[:2].upper()
def get_tiri(fid):
 try:
  d=cache.get(fid);now_t=time.time()
  if not d or now_t-d.get('time',0)>180:
   u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid)
   s=api_get(u)
   if s and len(s)>=2:
    sa=s[0].get('statistics',[]);sb=s[1].get('statistics',[])
    v1=get_stat(sa,'Shots on Goal');v2=get_stat(sb,'Shots on Goal')
    sot=v1+v2;cache[fid]={'sot':sot,'time':now_t};time.sleep(0.4);return sot
   if d: return d.get('sot',0)
   return 0
  return d.get('sot',0)
 except: return 0
def crea_bolla_15():
 try:
  OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
  u="https://v3.football.api-sports.io/fixtures?date="+OGGI
  fixtures=api_get(u)
  if not fixtures: return f"Nessuna partita oggi {OGGI}"
  picks=[];quota_tot=1.0
  fixtures=sorted(fixtures,key=lambda x: x["fixture"]["timestamp"])
  for p in fixtures:
   if len(picks)>=12: break
   if quota_tot>=3.35: break
   fid=p["fixture"]["id"];dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
   if dt < datetime.now(ITALY): continue
   home=p['teams']['home']['name'];away=p['teams']['away']['name'];paese=p['league']['country'];orario=dt.strftime("%H:%M")
   qenc=urllib.parse.quote(home+" "+away);link="https://www.bet365.it/#/AX/K^"+qenc
   u2="https://v3.football.api-sports.io/odds?fixture="+str(fid)
   odds=api_get(u2)
   if not odds or odds=="LIMIT": continue
   if not odds[0].get("bookmakers"): continue
   book=None
   for b in odds[0]["bookmakers"]:
    if b["id"]==8 or "365" in b["name"]: book=b;break
   if not book: book=odds[0]["bookmakers"][0]
   best=None
   for bet in book["bets"]:
    if bet["name"] not in ["Match Winner","Double Chance","Both Teams To Score","Goals Over/Under"]: continue
    for v in bet["values"]:
     try:
      q=float(v["odd"])
      if 1.08 <= q <= 1.30:
       if best is None or q>best["q"]: best={"m":bet["name"],"e":v["value"],"q":q}
     except: continue
   if not best: continue
   if quota_tot*best["q"]>3.45: continue
   m_name=best["m"];m_val=best["e"]
   if "Match Winner" in m_name: txt="VINCENTE: 1" if "Home" in m_val else "VINCENTE: 2" if "Away" in m_val else "VINCENTE: X"
   elif "Double Chance" in m_name:
    v=m_val.replace("Home/Draw","1X").replace("Draw/Away","X2").replace("Home/Away","12");txt="DOPPIA: "+v
   elif "Both Teams Score" in m_name: txt="GOL SI" if "Yes" in m_val else "GOL NO"
   else: txt=m_val+" GOL"
   quota_tot*=best["q"]
   riga=orario+" - "+paese+"\n"+home+" vs "+away+"\n-> "+txt+" @ "+str(best['q'])+"\n<a href='"+link+"'>Apri su BET365</a>"
   picks.append(riga)
  if len(picks)<5: return f"Poche partite {len(picks)} q {quota_tot:.2f}"
  return f"BOLLA {OGGI} Q {quota_tot:.2f}\n\n"+"\n\n".join(picks)+f"\n\nTOT {quota_tot:.2f}"
 except Exception as e: return f"Errore: {e}"
def poll_commands():
 global is_paused,last_update_id
 while True:
  try:
   url=f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25"
   r=requests.get(url,timeout=35).json()
   if r.get("ok"):
    for upd in r.get("result",[]):
     last_update_id=upd["update_id"];msg=upd.get("message",{});txt=msg.get("text","").lower().split("@")[0].strip();from_chat=msg.get("chat",{}).get("id")
     if "spegni" in txt or "pausa" in txt: is_paused=True;tg("PAUSA",from_chat,True)
     elif "accendi" in txt or "/start" in txt: is_paused=False;tg("RIPRESO",from_chat,True)
     elif "status" in txt:
      stato="PAUSA" if is_paused else "ATTIVO";ora=datetime.now(ITALY).strftime('%H:%M')
      tg(f"STATUS {stato} {ora} V13.7 FINAL",from_chat,True)
     elif "bolla" in txt: tg("Creo bolla...",from_chat);tg(crea_bolla_15(),from_chat,True)
  except: pass
  time.sleep(30 if is_paused else 2)
threading.Thread(target=poll_commands,daemon=True).start()
while True:
 try:
  if is_paused: time.sleep(60);continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0: av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
   time.sleep(600);continue
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT": time.sleep(3600);continue
  if not live: time.sleep(60);continue
  if time.time()-ultimo_invio_tripla>=3600 and len(tripla_coda)>=2:
   txt="TRIPLA "+now.strftime('%H:%M')+"\n\n"
   for p in tripla_coda[:3]: txt+=p['flag']+" "+p['pref']+" "+str(p['min'])+"'\n"
   tg(txt);tripla_coda=tripla_coda[3:];ultimo_invio_tripla=time.time()
  for g in live:
   fid=g["fixture"]["id"];st=g["fixture"]["status"]["short"];m=g["fixture"]["status"]["elapsed"]
   if m is None or fid in av_s: continue
   home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
   paese=g['league']['country'];flag=get_flag(paese);pref=flag+" "+paese
   if st=="HT" and fid not in pre1:
    so=get_tiri(fid)
    if so>=3: tg(f"FINE 1T {pref} {home} {gh}-{ga} {away} Tiri:{so}");pre1.add(fid)
   if 46<=m<=69 and fid not in pre:
    so=get_tiri(fid)
    if so>=5: tg(f"PREPARATI {m}' {pref} {home} {gh}-{ga} {away}");pre.add(fid)
   if 65<=m<=92:
    so=get_tiri(fid)
    if so>=4 and fid not in av_s:
     sq=home if gh<=ga else away;tg(f"GIOCALO {m}' {pref} {home} {gh}-{ga} {away} NEXT {sq}")
     av_s.add(fid);av_g[fid]=gh+ga
     if not any(x['fid']==fid for x in tripla_coda): tripla_coda.append({'fid':fid,'flag':flag,'pref':paese,'min':m,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})
  for g in live:
   fid=g["fixture"]["id"]
   if fid in av_g:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>av_g[fid]: tg(f"GOAL VINTO {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
  time.sleep(60)
 except: time.sleep(15)
