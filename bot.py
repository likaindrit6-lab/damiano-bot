import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
av_g={}
av_s=set()
pre=set()
pre1=set()
cache={}
tripla_coda=[]
ultimo_invio_tripla=time.time()
ultima_bolla_time=0
bolla_lock=False
ELITE_PAESI={"Italy","England","Spain","Germany","France","Portugal","Netherlands","Belgium","Turkey","Scotland","Austria","Switzerland","Denmark","Norway","Sweden","Poland","Greece","Croatia","Czech Republic","World"}
ELITE_LEGHE=["Champions League","Europa League","Conference League"]
try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except:
    pass
app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V21 - 70 SOLO - DC+MG1-5 COMBO VERA - {s}",200
def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()
TASTIERA_JSON=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BOLLA","STATUS"]],"resize_keyboard":True,"is_persistent":True})
def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        base=f"https://api.telegram.org/bot{BOT_TOKEN}"
        url=base+"/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera:
            payload["reply_markup"]=TASTIERA_JSON
        requests.post(url,json=payload,timeout=25)
    except:
        pass
def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429:
            return "LIMIT"
        return r.json().get("response",[])
    except:
        return []
def crea_bolla_15():
    global ultima_bolla_time
    try:
        if time.time() - ultima_bolla_time < 120:
            return None
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures:
            return f"Nessuna partita oggi {OGGI}"
        picks=[]
        quota_tot=1.0
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            if len(picks)>=30: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p["teams"]["home"]["name"]
            away=p["teams"]["away"]["name"]
            paese=p["league"]["country"]
            lega=p["league"]["name"]
            if paese not in ELITE_PAESI and not any(x in lega for x in ELITE_LEGHE):
                continue
            orario=dt.strftime("%H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue
            try:
                best=None
                # cerco in TUTTI i bookmaker la combo vera
                for book in odds[0]["bookmakers"]:
                    for bet in book["bets"]:
                        bn=bet["name"].lower()
                        # deve contenere doppia chance E multigol
                        if ("double chance" in bn or "chance" in bn) and ("multigol" in bn or "multi goal" in bn or "multi-goal" in bn or "goals" in bn):
                            for v in bet["values"]:
                                val=v["value"]
                                val_low=val.lower()
                                # deve essere 1-5
                                if "1-5" not in val and "1 - 5" not in val:
                                    continue
                                if "1x" in val_low or "home/draw" in val_low:
                                    txt="1X + Multigol 1-5"
                                elif "x2" in val_low or "draw/away" in val_low:
                                    txt="X2 + Multigol 1-5"
                                elif "12" in val_low or "home/away" in val_low:
                                    txt="12 + Multigol 1-5"
                                else:
                                    continue
                                try:
                                    q=float(v["odd"])
                                except:
                                    continue
                                if 1.05 <= q <= 3.0:
                                    if best is None or q>best["q"]:
                                        best={"txt":txt,"q":q}
                        # alcuni book chiamano "1X & Multigol 1-5"
                        if "1x" in bn and "1-5" in bn:
                            for v in bet["values"]:
                                if "1-5" in v["value"]:
                                    try:
                                        q=float(v["odd"])
                                        best={"txt":"1X + Multigol 1-5","q":q}
                                    except:
                                        pass
                if not best:
                    continue
                quota_tot*=best["q"]
                picks.append(f"{orario} - {paese} - {lega}\n{home} vs {away}\n-> {best['txt']} @ {best['q']}")
            except:
                continue
        if len(picks)<3:
            return f"Oggi poche ELITE con combo vera DC+MG1-5 su Planet style. Trovate {len(picks)} - quota {quota_tot:.2f}. Riprova piu tardi."
        ultima_bolla_time=time.time()
        return f"BOLLA ELITE DC+MG 1-5 (COMBO VERA) {OGGI} - Quota {quota_tot:.2f}\n\n"+"\n\n".join(picks)+f"\n\nTOT {quota_tot:.2f} - {len(picks)} partite"
    except Exception as e:
        return f"Errore bolla: {e}"
def poll_commands():
    global is_paused,last_update_id,bolla_lock
    while True:
        try:
            base=f"https://api.telegram.org/bot{BOT_TOKEN}"
            url=base+f"/getUpdates?offset={last_update_id+1}&timeout=25"
            r=requests.get(url,timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    msg=upd.get("message",{})
                    txt=msg.get("text","").lower().split("@")[0].strip()
                    from_chat=msg.get("chat",{}).get("id")
                    if "spegni" in txt or "pausa" in txt or "stop" in txt:
                        is_paused=True
                        tg("PAUSA",from_chat,con_tastiera=True)
                    elif "accendi" in txt or "riprendi" in txt or txt in ["/on","/start","on"]:
                        is_paused=False
                        tg("RIPRESO",from_chat,con_tastiera=True)
                    elif "status" in txt:
                        ora=datetime.now(ITALY).strftime('%H:%M')
                        st="PAUSA" if is_paused else "ATTIVO"
                        tg(f"{st} | {ora}",from_chat,con_tastiera=True)
                    elif "bolla" in txt or "bola" in txt:
                        if bolla_lock:
                            continue
                        bolla_lock=True
                        tg("Cerco combo vera PlanetWin365 style...",from_chat)
                        res=crea_bolla_15()
                        if res:
                            tg(res,from_chat,con_tastiera=True)
                        bolla_lock=False
        except:
            bolla_lock=False
            pass
        time.sleep(30 if is_paused else 2)
threading.Thread(target=poll_commands,daemon=True).start()
def get_stat(a, n):
    for s in a:
        t = s.get("type")
        if t == n:
            try:
                v = str(s.get("value") or 0).replace("%","").strip() or 0
                return int(v)
            except:
                return 0
    return 0
def get_flag(p):
    m={"Italy":"IT","England":"GB","Spain":"ES","Germany":"DE","France":"FR","Portugal":"PT","Netherlands":"NL","Belgium":"BE","Turkey":"TR"}
    return m.get(p,f"[{p}]")
while True:
    try:
        if is_paused:
            time.sleep(60)
            continue
        now=datetime.now(ITALY)
        if 0<=now.hour<10:
            if now.hour==0:
                av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
            time.sleep(600)
            continue
        live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live=="LIMIT":
            time.sleep(3600)
            continue
        if not live:
            time.sleep(60)
            continue
        if time.time()-ultimo_invio_tripla>=3600 and len(tripla_coda)>=2:
            txt=f"TRIPLA ORARIA {now.strftime('%H:%M')}\n\n"
            for p in tripla_coda[:3]:
                txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
            tg(txt)
            tripla_coda=tripla_coda[3:]
            ultimo_invio_tripla=time.time()
        for g in live:
            fid=g["fixture"]["id"]
            st=g["fixture"]["status"]["short"]
            mm=g["fixture"]["status"]["elapsed"]
            if mm is None or fid in av_s:
                continue
            home=g["teams"]["home"]["name"]
            away=g["teams"]["away"]["name"]
            gh=g["goals"]["home"]
            ga=g["goals"]["away"]
            paese=g["league"]["country"]
            lega=g["league"]["name"]
            flag=get_flag(paese)
            pref=f"{flag} {paese.upper()} - {lega}"
            def tiri():
                d=cache.get(fid)
                if not d or time.time()-d.get('time',0)>180:
                    s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if s and len(s)>=2:
                        sot=get_stat(s[0]["statistics"],"Shots on Goal")+get_stat(s[1]["statistics"],"Shots on Goal")
                        cache[fid]={"sot":sot,"time":time.time()}
                        time.sleep(0.4)
                        return sot
                    return d.get("sot",0) if d else 0
                return d.get("sot",0)
            if st=="HT" and fid not in pre1:
                so=tiri()
                if so>=3:
                    tg(f"FINE 1T {pref} | Tiri:{so} | {home} {gh}-{ga} {away}")
                    pre1.add(fid)
            if 46<=(mm or 0)<=69 and fid not in pre:
                so=tiri()
                if so>=5:
                    tg(f"PREPARATI {mm}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT")
                    pre.add(fid)
            if (mm or 0)==70 and fid not in av_s:
                so=tiri()
                if so>=4:
                    sq=home if gh<=ga else away
                    tg(f"GIOCALO {mm}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}")
                    av_s.add(fid)
                    av_g[fid]=gh+ga
                    if not any(x['fid']==fid for x in tripla_coda):
                        tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':mm,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})
        for g in live:
            fid=g["fixture"]["id"]
            if fid in av_g:
                tot=g["goals"]["home"]+g["goals"]["away"]
                if tot>av_g[fid]:
                    flag=get_flag(g["league"]["country"])
                    tg(f"GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                    del av_g[fid]
        time.sleep(60)
    except:
        time.sleep(15)
