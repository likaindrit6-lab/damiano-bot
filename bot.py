import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g={}; av_s=set(); pre=set(); pre1=set(); cache={}; tripla_coda=[]; ultimo_invio_tripla=time.time()

try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V28 UNDER 4.5 1.10-1.20 DAMI - {s}",200

def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({
    "keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"],["⚽ UNDER 4.5"]],
    "resize_keyboard":True,"is_persistent":True
})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        base=f"https://api.telegram.org/bot{BOT_TOKEN}"
        url=base+"/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA_JSON
        requests.post(url,json=payload,timeout=25)
    except: pass

def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

YOUTH_BLACKLIST=["U21","U20","U23","U19","U18","U17","YOUTH","PRIMAVERA","REVELACAO","RESERVA","RESERVE","WOMEN","FEMMINILE"]
def is_youth(lega): return any(b in lega.upper() for b in YOUTH_BLACKLIST)

def is_allowed_market(name):
    m=name.upper()
    if "CORNER" in m or "CARD" in m or "BOOKING" in m: return False
    if "SHOTS" in m or "PLAYER" in m or "SCORER" in m: return False
    if "1ST HALF" in m or "FIRST HALF" in m or "2ND HALF" in m or "SECOND HALF" in m: return False
    if any(x in m for x in ["MATCH WINNER","FULL TIME RESULT","1X2","ESITO FINALE"]): return True
    if "DOUBLE CHANCE" in m: return True
    if "BOTH TEAMS TO SCORE" in m or "BTTS" in m: return True
    if "OVER/UNDER" in m or "TOTAL GOALS" in m: return True
    if "DRAW NO BET" in m or m=="DNB": return True
    if "HT/FT" in m or "HALF TIME/FULL TIME" in m: return True
    return False

def traduci(market, sel):
    mk=market.upper()
    s=sel.upper().replace("HOME/DRAW","1X").replace("DRAW/AWAY","X2").replace("HOME/AWAY","12").replace("HOME","1").replace("AWAY","2").replace("DRAW","X").replace("YES","SI")
    if "DOUBLE CHANCE" in mk: return f"DOPPIA CHANCE: {s}"
    if "BOTH TEAMS" in mk or "BTTS" in mk: return f"GOL: {'SI' if 'SI' in s else 'NO'}"
    if "DRAW NO BET" in mk or "DNB" in mk: return f"DNB: {s} (PAREGGIO RIMBORSATO)"
    if "HT/FT" in mk: return f"PARZIALE/FINALE: {s}"
    if "OVER/UNDER" in mk or "TOTAL" in mk: return f"UNDER/OVER: {sel}"
    return f"ESITO FINALE: {s}"

def lista_under_35():
    try:
        now = datetime.now(ITALY)
        fine_24h = now + timedelta(hours=24)
        OGGI = now.strftime("%Y-%m-%d")
        DOMANI = fine_24h.strftime("%Y-%m-%d")
        fixtures_oggi = api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        fixtures_domani = api_get(f"https://v3.football.api-sports.io/fixtures?date={DOMANI}")
        fixtures = []
        if fixtures_oggi and fixtures_oggi!= "LIMIT": fixtures += fixtures_oggi
        if fixtures_domani and fixtures_domani!= "LIMIT" and DOMANI!= OGGI: fixtures += fixtures_domani
        if not fixtures: return f"Nessuna partita nelle prossime 24H"
        risultati=[]
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < now: continue
            if dt > fine_24h: continue
            if is_youth(p['league']['name']): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']; orario=dt.strftime("%d/%m %H:%M")
            qenc=urllib.parse.quote_plus(home+" "+away)
            link_bet365=f"https://www.bet365.it/search?q={qenc}"
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue
            book_to_use = odds[0]["bookmakers"][0]
            try:
                for bet in book_to_use["bets"]:
                    if "OVER/UNDER" not in bet["name"].upper() and "TOTAL" not in bet["name"].upper(): continue
                    for v in bet["values"]:
                        if "under 4.5" in v["value"].lower():
                            try:
                                q=float(v["odd"])
                                if q >= 1.10 and q <= 1.20:
                                    risultati.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 UNDER 4.5 @ {q}\n<a href='{link_bet365}'>BET365</a>")
                            except: pass
            except: continue
            time.sleep(0.2)
        if not risultati: return f"Nessuna Under 4.5 1.10-1.20 nelle prossime 24H"
        return f"⚽ UNDER 4.5 1.10-1.20 - PROSSIME 24H ({len(risultati)} partite)\nDa {now.strftime('%H:%M')} a {fine_24h.strftime('%d/%m %H:%M')}\n\n" + "\n\n".join(risultati)
    except Exception as e: return f"Errore under: {e}"

def crea_bolla_15():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures: return f"Nessuna partita oggi {OGGI}"
        picks=[]; quota_tot=1.0
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            if len(picks)>=10 or quota_tot>=3.50: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            if is_youth(p['league']['name']): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']; orario=dt.strftime("%H:%M")
            qenc=urllib.parse.quote_plus(home+" "+away)
            link_bet365=f"https://www.bet365.it/search?q={qenc}"
            link_stats=f"https://www.flashscore.it/search/?q={qenc}"
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue
            bk365=None
            for bk in odds[0]["bookmakers"]:
                if bk.get("id")==8: bk365=bk; break
            book_to_use=bk365 if bk365 else odds[0]["bookmakers"][0]
            try:
                best=None; best_market=""
                for bet in book_to_use["bets"]:
                    if not is_allowed_market(bet["name"]): continue
                    for v in bet["values"]:
                        try:
                            q=float(v["odd"])
                            if 1.15 <= q <= 1.40 and (best is None or q>best["q"]):
                                best={"e":v["value"],"q":q}; best_market=bet["name"]
                        except: continue
                if not best: continue
                if quota_tot*best["q"]>3.60: continue
                txt=traduci(best_market,best["e"])
                quota_tot*=best["q"]
                picks.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 {txt} @ {best['q']}\n<a href='{link_bet365}'>BET365</a> | <a href='{link_stats}'>STATS</a>")
            except: continue
        if len(picks)<4: return f"Oggi poche partite prime squadre, riprova tra 1h. Trovate {len(picks)} quota {quota_tot:.2f}"
        if quota_tot<2.80: return f"Poche quote, trovate {len(picks)} quota {quota_tot:.2f}"
        return f"🔥 BOLLA DAMI 80%+ {OGGI} - Quota {quota_tot:.2f} 🔥\n\n"+"\n\n".join(picks)+f"\n\n💰 TOT {quota_tot:.2f} - {len(picks)} partite - SOLO BET365"
    except Exception as e: return f"Errore bolla: {e}"

def poll_commands():
    global is_paused,last_update_id
    while True:
        try:
            base=f"https://api.telegram.org/bot{BOT_TOKEN}"
            url=base+f"/getUpdates?offset={last_update_id+1}&timeout=25"
            r=requests.get(url,timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    msg=upd.get("message",{}); txt=msg.get("text","").lower().split("@")[0].strip()
                    from_chat=msg.get("chat",{}).get("id")
                    if "spegni" in txt or txt.startswith("/pausa") or txt in ["pausa","stop","🔴 spegni"]:
                        is_paused=True; tg("🛑 PAUSA",from_chat,con_tastiera=True)
                    elif "accendi" in txt or txt.startswith("/riprendi") or txt in ["/on","/start","on","🟢 accendi"]:
                        is_paused=False; tg("✅ RIPRESO",from_chat,con_tastiera=True)
                    elif "status" in txt:
                        ora=datetime.now(ITALY).strftime('%H:%M'); st="PAUSA" if is_paused else "ATTIVO"
                        tg(f"📊 {st} | {ora}",from_chat,con_tastiera=True)
                    elif "under" in txt:
                        tg("⏳ Cerco Under 4.5 1.10-1.20 - 24H...",from_chat)
                        tg(lista_under_35(),from_chat,con_tastiera=True)
                    elif "bolla" in txt or "bola" in txt:
                        tg("⏳ Creo bolla solo prime squadre Bet365...",from_chat)
                        tg(crea_bolla_15(),from_chat,con_tastiera=True)
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
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷"}
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
        for g in live:
            fid=g["fixture"]["id"]; st=g["fixture"]["status"]["short"]; m=g["fixture"]["status"]["elapsed"]
            if m is None or fid in av_s: continue
            if is_youth(g['league']['name']): continue
            home=g['teams']['home']['name']; away=g['teams']['away']['name']
            gh=g['goals']['home']; ga=g['goals']['away']; paese=g['league']['country']; lega=g['league']['name']
            flag=get_flag(paese); pref=f"{flag} {paese.upper()} - {lega}"
            def tiri():
                d=cache.get(fid)
                if not d or time.time()-d.get('time',0)>180:
                    s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if s and len(s)>=2:
                        sot=get_stat(s[0]['statistics'],'Shots on Goal')+get_stat(s[1]['statistics'],'Shots on Goal')
                        cache[fid]={'sot':sot,'time':time.time()}; time.sleep(0.4); return sot
                    return d.get('sot',0) if d else 0
                return d.get('sot',0)
            if st=="HT" and fid not in pre1:
                so=tiri()
                if so>=3: tg(f"⏸️ FINE 1T {pref} | Tiri:{so} | {home} {gh}-{ga} {away}"); pre1.add(fid)
            if 46<=(m or 0)<=69 and fid not in pre:
                so=tiri()
                if so>=5: tg(f"🔔 PREPARATI {m}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT"); pre.add(fid)
            if 65<=(m or 0)<=92:
                so=tiri()
                if so>=4 and fid not in av_s:
                    sq=home if gh<=ga else away
                    tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}")
                    av_s.add(fid); av_g[fid]=gh+ga
        for g in live:
            fid=g["fixture"]["id"]
            if fid in av_g:
                tot=g["goals"]["home"]+g["goals"]["away"]
                if tot>av_g[fid]:
                    flag=get_flag(g['league']['country'])
                    tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                    del av_g[fid]
        time.sleep(60)
    except: time.sleep(15)
