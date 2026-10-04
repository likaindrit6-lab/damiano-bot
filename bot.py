import os,time,requests,threading,random
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused = False
last_update_id = 0
# --- NUOVO PER BOLLA ---
bolla_attiva=[]
bolla_attiva_info={}
bolla_creata_ora=0

try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    stato_bolla = f" | Bolla: {len(bolla_attiva)} partite" if bolla_attiva else " | Bolla: nessuna"
    return f"BOT V10 BOLLA + V9 - {'PAUSA ⏸️ 0 richieste' if is_paused else 'ATTIVO ✅'}{stato_bolla}", 200

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
    global is_paused, last_update_id, bolla_attiva, bolla_attiva_info, bolla_creata_ora
    while True:
        try:
            sleep_time = 30 if is_paused else 2
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25"
            r = requests.get(url, timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result", []):
                    last_update_id = upd["update_id"]
                    msg = upd.get("message", {})
                    txt = msg.get("text","").lower().split("@")[0].strip()
                    from_chat = msg.get("chat",{}).get("id")
                    if txt.startswith("/pausa") or txt in ["pausa","stop"]:
                        is_paused=True; tg("🛑 PAUSA V10 - Ora consumo 0. Scrivo solo /riprendi quando vuoi", from_chat)
                    elif txt.startswith("/riprendi") or txt in ["riprendi","/on","/start","on"]:
                        is_paused=False; tg("✅ RIPRESO - Segnali + Tripla + Bolla ON", from_chat)
                    elif txt.startswith("/status"):
                        tg(f"📊 {'PAUSA - 0 consumo' if is_paused else 'ATTIVO'} | Ora: {datetime.now(ITALY).strftime('%H:%M')} | Tripla in coda: {len(tripla_coda)}/3 | Bolla: {len(bolla_attiva)} partite", from_chat)
                    # --- NUOVO COMANDO SCHEDINA ---
                    elif txt.startswith("/schedina") or txt.startswith("/bolla"):
                        if bolla_attiva:
                            # manda quella già attiva
                            txt_b = f"🎫 <b>BOLLA ATTIVA X2 - {len(bolla_attiva)} partite</b>\nInizio tra poco:\n\n"
                            for i,p in enumerate(bolla_attiva,1):
                                txt_b+=f"{i}. {p['flag']} {p['home']} - {p['away']} -> <b>X2</b> ({p['orario']})\n"
                            txt_b+=f"\n💰 Quota totale ~{1.45**len(bolla_attiva):.2f} | Stake 1.60\n⏳ Ti avviso io alla fine se VINTA/PERSA"
                            tg(txt_b, from_chat)
                        else:
                            tg("⏳ Creo nuova BOLLA pre-partita X2 (solo partite non iniziate)...", from_chat)
                            crea_nuova_bolla(from_chat)
        except: pass
        time.sleep(30 if is_paused else 2)

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

# --- FUNZIONI NUOVE BOLLA (NON TOCCANO IL RESTO) ---
def crea_nuova_bolla(chat_id=None):
    global bolla_attiva, bolla_attiva_info, bolla_creata_ora
    try:
        oggi = datetime.now(ITALY).strftime("%Y-%m-%d")
        domani = (datetime.now(ITALY)+timedelta(days=1)).strftime("%Y-%m-%d")
        fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
        if fixtures=="LIMIT": tg("⚠️ Limite API raggiunto, riprovo dopo", chat_id); return
        # filtra solo Non Started e tra 15 min e 4 ore
        candidati=[]
        now_utc = datetime.now(timezone.utc)
        for f in fixtures:
            if f["fixture"]["status"]["short"]!="NS": continue
            try:
                kickoff = datetime.fromisoformat(f["fixture"]["date"].replace("Z","+00:00"))
                diff_min = (kickoff - now_utc).total_seconds()/60
                if 15 <= diff_min <= 240:
                    candidati.append(f)
            except: continue
        if len(candidati)<5:
            # prova anche domani
            fixtures2 = api_get(f"https://v3.football.api-sports.io/fixtures?date={domani}")
            if fixtures2!="LIMIT":
                for f in fixtures2:
                    if f["fixture"]["status"]["short"]=="NS":
                        candidati.append(f)

        if len(candidati)<5:
            tg("❌ Poche partite pre-match ora, riprovo tra 1 ora", chat_id); return

        scelti = random.sample(candidati, min(6, len(candidati)))
        bolla_attiva=[]
        txt = f"🎫🎫🎫 <b>BOLLA PRE-PARTITA X2 - {len(scelti)} PARTITE</b> 🎫🎫🎫\n"
        txt+= f"Inizio tra 15-180 min | Stake consigliato 1.60U\n\n"
        quota_tot=1
        for i,f in enumerate(scelti,1):
            flag=get_flag(f["league"]["country"])
            home=f["teams"]["home"]["name"]; away=f["teams"]["away"]["name"]
            orario = f["fixture"]["date"][11:16]
            lega = f["league"]["name"]
            txt+=f"{i}. {flag} {home} - {away} -> <b>X2</b> ({lega} {orario})\n"
            bolla_attiva.append({
                "fid": f["fixture"]["id"],
                "home": home, "away": away,
                "flag": flag, "lega": lega,
                "orario": orario,
                "esito": None, # WIN/LOSE
                "finale": ""
            })
            quota_tot*=1.42

        txt+=f"\n💰 Quota totale stimata ~{quota_tot:.2f}\n"
        txt+=f"⏰ Ti avviso io alla fine con VINTO/PERSO di ogni partita + finale BOLLA"
        tg(txt, chat_id)
        bolla_creata_ora=time.time()
        bolla_attiva_info={"quota":quota_tot}
        print(f"BOLLA CREATA {len(bolla_attiva)}", flush=True)
    except Exception as e:
        print(f"Err bolla {e}", flush=True)

def check_bolla_finale():
    global bolla_attiva
    if not bolla_attiva: return
    try:
        finite=0; vinte=0
        dettaglio=""
        for p in bolla_attiva:
            # controlla risultato finale
            if p["esito"] is None:
                res = api_get(f"https://v3.football.api-sports.io/fixtures?id={p['fid']}")
                if res and res!="LIMIT":
                    f=res[0]
                    status=f["fixture"]["status"]["short"]
                    if status in ["FT","AET","PEN"]:
                        gh=f["goals"]["home"]; ga=f["goals"]["away"]
                        # X2 = pareggio o vince Away
                        if ga>=gh: # X2 vinto (X o 2)
                            p["esito"]="WIN"
                            vinte+=1
                            dettaglio+=f"✅ {p['flag']} {p['home']} {gh}-{ga} {p['away']} -> X2 VINTO\n"
                        else:
                            p["esito"]="LOSE"
                            dettaglio+=f"❌ {p['flag']} {p['home']} {gh}-{ga} {p['away']} -> X2 PERSO\n"
                        p["finale"]=f"{gh}-{ga}"
                        finite+=1
                        time.sleep(0.3)
                    else:
                        # ancora in corso
                        pass
                else:
                    time.sleep(0.3)
            else:
                finite+=1
                if p["esito"]=="WIN": vinte+=1

        # se tutte finite
        if finite==len(bolla_attiva) and len(bolla_attiva)>0:
            if vinte==len(bolla_attiva):
                tg(f"🎉🎉🎉 <b>CONGRATULAZIONI! BOLLA VINTA! {vinte}/{len(bolla_attiva)}!</b> 🎉🎉🎉\n\n{dettaglio}\n💰 +{bolla_attiva_info.get('quota',6):.2f}U con stake 1.60!")
            else:
                tg(f"❌ <b>BOLLA PERSA - {vinte} vinte / {len(bolla_attiva)-vinte} persa</b>\n\n{dettaglio}\n💔 Riprovo con la prossima bolla tra poco")
            print(f"BOLLA CHIUSA {vinte}/{len(bolla_attiva)}", flush=True)
            bolla_attiva=[] # resetta
    except Exception as e:
        print(f"Err check bolla {e}", flush=True)

av_g,av_s,pre,pre1,cache={},set(),set(),set(),{}
tripla_coda=[]
ultimo_invio_tripla=time.time()
print("BOT V10 BOLLA + V9 DOPPIA - ATTIVO",flush=True)

while True:
 try:
  if is_paused:
      print("PAUSA - dormo 60 sec - 0 richieste API-Football", flush=True)
      time.sleep(60); continue
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:
    av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
   time.sleep(600); continue

  # --- CHECK BOLLA OGNI 3 MIN ---
  if bolla_attiva:
      check_bolla_finale()
  else:
      # auto-crea una bolla ogni 4 ore se non c'è
      if time.time()-bolla_creata_ora>14400:
          crea_nuova_bolla()

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
      print(f"TRIPLA INVIATA {len(tripla_coda[:3])}", flush=True)
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
