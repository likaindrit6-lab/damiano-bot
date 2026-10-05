import os,time,requests,threading
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused = False
last_update_id = 0
av_g,av_s,pre,pre1,cache={},set(),set(),set(),{}
tripla_coda=[]
ultimo_invio_tripla=time.time()

try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    return f"BOT V10 DOPPIA+BOLLA 1.80 - {'PAUSA' if is_paused else 'ATTIVO'}", 200

def run_flask():
    from waitress import serve
    serve(app, host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

def tg(m, chat_id=None):
 try:
  cid = chat_id if chat_id else CHAT_ID
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":cid,"text":m,"parse_mode":"HTML"},timeout=25)
 except: pass

def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []

# --- BOLLA ODIERNA QUOTA 1.80 - 80/85% ---
def crea_bolla_180():
    try:
        OGGI = datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures:
            return f"⚠️ Nessuna partita oggi {OGGI}"

        picks=[]
        quota_tot=1.0
        mercati_sicuri = ["Match Winner", "Double Chance", "Goals Over/Under", "Team To Score", "Home Team Over/Under", "Away Team Over/Under"]

        # ordina per orario
        fixtures = sorted(fixtures, key=lambda x: x["fixture"]["timestamp"])

        for p in fixtures:
            if len(picks)>=4: break
            if quota_tot>=1.85: break

            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"], tz=ITALY)
            if dt < datetime.now(ITALY): continue
            if dt.hour < 10: continue

            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            orario=dt.strftime("%H:%M")

            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue

            try:
                bets=odds[0]["bookmakers"][0]["bets"]
                best=None
                for bet in bets:
                    if bet["name"] not in mercati_sicuri:
                        # permetti anche mercati simili bassi
                        if "Over/Under" not in bet["name"] and "Double" not in bet["name"] and "Winner" not in bet["name"]:
                            continue
                    if "First Half" in bet["name"]: continue
                    if "Corners" in bet["name"]: continue
                    if "Cards" in bet["name"]: continue

                    for v in bet["values"]:
                        try:
                            q=float(v["odd"])
                            # SOLO QUOTE BASSE 80-85%
                            if 1.10 <= q <= 1.32:
                                # evita quote inutili tipo Over 0.5 a 1.05
                                if q < 1.10: continue
                                # scegli la quota più alta tra le sicure
                                if best is None or q > best["q"]:
                                    best={"mercato":bet["name"], "esito":v["value"], "q":q}
                        except: continue

                if not best: continue
                # non sforare 1.90
                if quota_tot * best["q"] > 1.90: continue

                quota_tot *= best["q"]
                picks.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 {best['mercato']}: {best['esito']} @ {best['q']}")
            except: continue

        if len(picks) < 2:
            return f"Oggi {OGGI} ho trovato {len(fixtures)} partite ma poche con quota 80%. Riprova tra 1 ora, ne arrivano altre."

        txt=f"🔥 BOLLA ODIERNA 80/85% - {OGGI} - Quota {quota_tot:.2f} 🔥\n\n" + "\n\n".join(picks) + f"\n\n💰 QUOTA TOT: {quota_tot:.2f} ({len(picks)} partite)\n🎯 Obiettivo: 1.80"
        return txt
    except Exception as e:
        return f"Errore bolla: {e}"

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
                        is_paused=True; tg("🛑 PAUSA V10 - 0 richieste", from_chat)
                    elif txt.startswith("/riprendi") or txt in ["riprendi","/on","/start","on"]:
                        is_paused=False; tg("✅ RIPRESO - Live + Tripla + Bolla 1.80 ON", from_chat)
                    elif txt.startswith("/status"):
                        tg(f"📊 {'PAUSA' if is_paused else 'ATTIVO'} | {datetime.now(ITALY).strftime('%H:%M')} | Tripla: {len(tripla_coda)}/3", from_chat)
                    elif "bolla" in txt:
                        tg("⏳ Cerco bolla odierna quota 1.80 con mercati 80%...", from_chat)
                        tg(crea_bolla_180(), from_chat)
        except: pass
        time.sleep(30 if is_paused else 2)

threading.Thread(target=poll_commands,daemon=True).start()

def get_stat(a,n):
 for s in a:
  if s.get('type')==n:
   try: return int(str(s.get('value') or 0).replace('%','').strip() or 0)
   except: return 0
 return 0

def get_flag(p):
 m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸","Australia":"🇦🇺","Japan":"🇯🇵","South Korea":"🇰🇷"}
 return m.get(p,f"[{p}]")

print("BOT V10 DOPPIA+BOLLA 1.80",flush=True)

while True:
 try:
  if is_paused:
      print("PAUSA - 0 richieste", flush=True)
      time.sleep(60); continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:
    av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
   time.sleep(600); continue

  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT": time.sleep(3600); continue
  if not live: time.sleep(60); continue

  if time.time() - ultimo_invio_tripla >= 3600 and len(tripla_coda) >= 2:
      txt = f"🔥🔥🔥 TRIPLA ORARIA QUOTA 3 - {now.strftime('%H:%M')} 🔥🔥🔥\n\n"
      quota=1
      for p in tripla_coda[:3]:
          txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
          quota*=1.45
      txt+=f"\n💰 QUOTA TOT ~{quota:.2f} - Gioca Next Goal"
      tg(txt)
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
    if so>=4:
     if fid not in av_s:
      sq=home if gh<=ga else away
      tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}")
      av_s.add(fid);av_g[fid]=gh+ga
      if not any(x['fid']==fid for x in tripla_coda):
          tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':m,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})

  for g in live:
   fid=g["fixture"]["id"]
   if fid in av_g:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>av_g[fid]:
     flag=get_flag(g['league']['country']);tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
  time.sleep(60)
 except:
  time.sleep(15)
