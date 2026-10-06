import os,time,requests,threading,json,urllib.parse
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
    return f"BOT V13-BET365 LINK - {'PAUSA' if is_paused else 'ATTIVO'}", 200

def run_flask():
    from waitress import serve
    serve(app, host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON = json.dumps({
    "keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"]],
    "resize_keyboard":True,
    "is_persistent":True
})

def tg(m, chat_id=None, con_tastiera=False):
 try:
  cid = chat_id if chat_id else CHAT_ID
  payload={"chat_id":cid,"text":m,"parse_mode":"HTML", "disable_web_page_preview": True}
  if con_tastiera:
      payload["reply_markup"]=TASTIERA_JSON
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json=payload,timeout=25)
 except: pass

def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []

def crea_bolla_15():
    try:
        OGGI = datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures: return f"Nessuna partita oggi {OGGI}"
        picks=[]; quota_tot=1.0
        fixtures = sorted(fixtures, key=lambda x: x["fixture"]["timestamp"])
        for p in fixtures:
            if len(picks)>=12: break
            if quota_tot>=3.35: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"], tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            orario=dt.strftime("%H:%M")

            # LINK DIRETTO BET365 - ti apre la ricerca della partita
            query = urllib.parse.quote(f"{home} {away}")
            link_bet365 = f"https://www.bet365.it/#/AX/K^{query}"

            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue

            book=None
            for b in odds[0]["bookmakers"]:
                if b["id"]==8 or "365" in b["name"]:
                    book=b; break
            if not book: book=odds[0]["bookmakers"][0]

            try:
                best=None
                for bet in book["bets"]:
                    if bet["name"] not in ["Match Winner", "Double Chance", "Both Teams To Score", "Goals Over/Under"]:
                        continue
                    for v in bet["values"]:
                        try:
                            q=float(v["odd"])
                            if 1.08 <= q <= 1.30:
                                if best is None or q > best["q"]:
                                    best={"m":bet["name"],"e":v["value"],"q":q}
                        except: continue
                if not best: continue
                if quota_tot*best["q"]>3.45: continue
                m_name=best["m"]; m_val=best["e"]
                if "Match Winner" in m_name:
                    if "Home" in m_val: txt="VINCENTE FINALE: 1"
                    elif "Away" in m_val: txt="VINCENTE FINALE: 2"
                    else: txt="VINCENTE FINALE: X"
                elif "Double Chance" in m_name:
                    v=m_val.replace("Home/Draw","1X").replace("Draw/Away","X2").replace("Home/Away","12")
                    txt=f"DOPPIA CHANCE: {v}"
                elif "Both Teams Score" in m_name:
                    txt="GOL: SI" if "Yes" in m_val else "GOL: NO"
                else:
                    txt=f"{m_val} GOL"
                quota_tot*=best["q"]
                # AGGIUNTO LINK CLICCABILE
                picks.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 {txt} @ {best['q']}\n🔗 <a href='{link_bet365}'>Apri su BET365</a>")
            except: continue

        if len(picks) < 5:
            return f"Oggi poche partite BET365, riprova tra 1h. Trovate {len(picks)} per quota {quota_tot:.2f}"
        if len(picks) == 5 and quota_tot < 3.00:
            return f"Oggi poche partite BET365, riprova tra 1h. Trovate {len(picks)} per quota {quota_tot:.2f} - aspetto 3.00"

        return f"🔥 BOLLA BET365 80%+ {OGGI} - Quota {quota_tot:.2f} 🔥\n\n" + "\n\n".join(picks) + f"\n\n💰 TOT {quota_tot:.2f} - {len(picks)} partite - OBIETTIVO 3.20/3.30"
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
                    if "spegni" in txt or txt.startswith("/pausa") or txt in ["pausa","stop","🔴 spegni"]:
                        is_paused=True; tg("🛑 PAUSA", from_chat, con_tastiera=True)
                    elif "accendi" in txt or txt.startswith("/riprendi") or txt in ["/on","/start","on","🟢 accendi"]:
                        is_paused=False; tg("✅ RIPRESO", from_chat, con_tastiera=True)
                    elif "status" in txt:
                        tg(f"📊 {'PAUSA' if is_paused else 'ATTIVO'} | {datetime.now(ITALY).strftime('%H:%M')}", from_chat, con_tastiera=True)
                    elif "bolla" in txt or "bola" in txt:
                        tg("⏳ Creo bolla BET365 con link diretti...", from_chat)
                        tg(crea_bolla_15(), from_chat, con_tastiera=True)
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

while True:
 try:
  if is_paused: time.sleep(60); continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0: av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
   time.sleep(600); continue
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT": time.sleep(3600); continue
  if not live: time.sleep(60); continue
  if time.time() - ultimo_invio_tripla >= 3600 and len(tripla_coda) >= 2:
      txt = f"🔥🔥🔥 TRIPLA ORARIA {now.strftime('%H:%M')} 🔥🔥🔥\n\n"
      for p in tripla_coda[:3]:
          txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
      tg(txt)
      tripla_coda = tripla_coda[3:]
      ultimo_invio_tripla = time.time()
