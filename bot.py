import os,time,requests,threading
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused = False
last_update_id = 0

try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    return f"BOT V8 DOPPIA OK - {'PAUSA' if is_paused else 'ATTIVO'}", 200

def run_flask():
    from waitress import serve
    serve(app, host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

def tg(m, chat_id=None):
 try:
  cid = chat_id if chat_id else CHAT_ID
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":cid,"text":m,"parse_mode":"HTML"},timeout=25)
 except: pass

def poll_commands():
    global is_paused, last_update_id
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25"
            r = requests.get(url, timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result", []):
                    last_update_id = upd["update_id"]
                    msg = upd.get("message", {})
                    txt = msg.get("text","").lower().split("@")[0].strip()
                    from_chat = msg.get("chat",{}).get("id")
                    if txt.startswith("/pausa") or txt in ["pausa","stop"]:
                        is_paused=True; tg("🛑 PAUSA - 0 token", from_chat)
                    elif txt.startswith("/riprendi") or txt in ["riprendi","/on","/start","on"]:
                        is_paused=False; tg("✅ RIPRESO - Segnali + Tripla oraria ON", from_chat)
                    elif txt.startswith("/status"):
                        tg(f"📊 {'PAUSA' if is_paused else 'ATTIVO'} | Ora: {datetime.now(ITALY).strftime('%H:%M')} | Tripla in coda: {len(tripla_coda)}/3", from_chat)
        except: pass
        time.sleep(2)
threading.Thread(target=poll_commands,daemon=True).start()

def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []

def get_stat(a,n):
 for s in a:
  if s.get('type')==n:
   try: return int(str(s.get('value') or 0).replace('%','').strip() or 0)
   except: return 0
 return 0

def get_flag(p):
 m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸","Australia":"🇦🇺","Japan":"🇯🇵","South Korea":"🇰🇷"}
 return m.get(p,f"[{p}]")

av_g,av_s,pre,pre1,cache={},set(),set(),set(),{}
tripla_coda=[]
ultimo_invio_tripla=time.time()
print("BOT V8 DOPPIA - SEGNALI + TRIPLA ORARIA",flush=True)

while True:
 try:
  if is_paused:
      time.sleep(15); continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:
    av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
   time.sleep(600); continue

  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT": time.sleep(3600); continue
  if not live: time.sleep(60); continue

  # --- OGNI ORA SPARA TRIPLA SE CE NE SONO 2-3 ---
  if time.time() - ultimo_invio_tripla >= 3600 and len(tripla_coda) >= 2:
      txt = f"🔥🔥🔥 TRIPLA ORARIA QUOTA 3 - {now.strftime('%H:%M')} 🔥🔥🔥\n\n"
      quota=1
      for p in tripla_coda[:3]:
          txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
          quota*=1.45
      txt+=f"\n💰 QUOTA TOT ~{quota:.2f} - Gioca Next Goal"
      tg(txt)
      print(f"TRIPLA INVIATA {len(tripla_coda[:3])}",flush=True)
      tripla_coda = tripla_coda[3:]
      ultimo_invio_tripla = time.time()

  for g in live:
   fid=g["fixture"]["id"];st=g["fixture"]["status"]["short"];m=g["fixture"]["status"]["elapsed"]
   if m is None or fid in av_s: continue
   home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away'];paese=g['league']['country'];lega=g['league']['name'];flag=get_flag(paese);pref=f"{flag} {paese.upper()} - {lega}"
   def tiri():
    d=cache.get(fid)
    if not d or time.time()-d.get('time',0)>180:
     s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if s and len(s)>=2:
      sot=get_stat(s[0]['statistics'],'Shots on Goal')+get_stat(s[1]['statistics'],'Shots on Goal');cache[fid]={'sot':sot,'time':time.time()};time.sleep(0.4);return sot
     return d.get('sot',0) if d else 0
    return d.get('sot',0)

   # 1) SEGNALI NORMALI COME PRIMA - LI VEDI SUBITO
   if st=="HT" and fid not in pre1:
    so=tiri()
    if so>=3: tg(f"⏸️ FINE 1T {pref} | Tiri:{so} | {home} {gh}-{ga} {away}");pre1.add(fid)

   if 46<=(m or 0)<=69 and fid not in pre:
    so=tiri()
    if so>=5:
     tg(f"🔔 PREPARATI {m}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT")
     pre.add(fid)

   if 65<=(m or 0)<=92:
    so=tiri()
    if so>=4: # PIANO A - SOT 4 dal 65'
     if fid not in av_s:
      # SEGNALE ISTANTANEO
      sq=home if gh<=ga else away
      tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}")
      av_s.add(fid);av_g[fid]=gh+ga
      # IN PIÙ LO AGGIUNGE ALLA TRIPLA ORARIA
      if not any(x['fid']==fid for x in tripla_coda):
          tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':m,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})
          print(f"Aggiunta tripla {len(tripla_coda)}/3", flush=True)

  for g in live:
   fid=g["fixture"]["id"]
   if fid in av_g:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>av_g[fid]:
     flag=get_flag(g['league']['country']);tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
  time.sleep(60)
 except:
  time.sleep(15)
