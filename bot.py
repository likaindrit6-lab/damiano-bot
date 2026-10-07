import os,time,requests,threading,json,urllib.parse
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

try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V19 LIVE FIX - {s}",200

def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({
    "keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","⬇️ UNDER"],["📊 STATUS"]],
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

def crea_bolla_15():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures: return f"Nessuna partita oggi {OGGI}"
        picks=[]; quota_tot=1.0
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            if len(picks)>=12 or quota_tot>=3.35: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            orario=dt.strftime("%H:%M")
            qenc=urllib.parse.quote_plus(home+" "+away)
            qenc_bet=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
            link_bet365=f"https://www.google.com/search?q={qenc_bet}&btnI=1"
            link_stats=f"https://www.flashscore.it/search/?q={qenc}"
            link_google=f"https://www.google.com/search?q={qenc}+pronostico&udm=14"
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            try:
                best=None
                for bet in odds[0]["bookmakers"][0]["bets"]:
                    if "First Half" in bet["name"] or "Corners" in bet["name"] or "Cards" in bet["name"]: continue
                    for v in bet["values"]:
                        try:
                            q=float(v["odd"])
                            if 1.08 <= q <= 1.30 and (best is None or q > best["q"]):
                                best={"m":bet["name"],"e":v["value"],"q":q}
                        except: continue
                if not best or quota_tot*best["q"]>3.45: continue
                m_name=best["m"]; m_val=best["e"]
                if "Match Winner" in m_name: txt="VINCENTE FINALE: 1" if "Home" in m_val else "VINCENTE FINALE: 2" if "Away" in m_val else "VINCENTE FINALE: X"
                elif "Double Chance" in m_name: txt=f"DOPPIA CHANCE: {m_val.replace('Home/Draw','1X').replace('Draw/Away','X2').replace('Home/Away','12')}"
                elif "Both Teams Score" in m_name: txt="GOL: SI" if "Yes" in m_val else "GOL: NO"
                elif "Over/Under" in m_name: txt=f"{m_val} GOL"
                else: txt=f"{m_name}: {m_val}"
                quota_tot*=best["q"]
                picks.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 {txt} @ {best['q']}\n<a href='{link_bet365}'>BET365</a> | <a href='{link_stats}'>STATS</a> | <a href='{link_google}'>GOOGLE</a>")
            except: continue
        if len(picks)<5: return f"Oggi poche partite da 80%, riprova tra 1h. Trovate {len(picks)} per quota {quota_tot:.2f}"
        return f"🔥 BOLLA ODIERNA 80%+ {OGGI} - Quota {quota_tot:.2f} 🔥\n\n"+"\n\n".join(picks)+f"\n\n💰 TOT {quota_tot:.2f} - {len(picks)} partite"
    except Exception as e: return f"Errore bolla: {e}"

def crea_bolla_under():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures: return f"Nessuna partita oggi {OGGI}"
        picks=[]
        for p in fixtures:
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue
            for bet in odds[0]["bookmakers"][0]["bets"]:
                if "Over/Under" in bet["name"] and "4.5" in str(bet["values"]):
                    for v in bet["values"]:
                        if "Under 4.5" in v["value"]:
                            try:
                                q=float(v["odd"])
                                if q < 1.20:
                                    orario=dt.strftime("%H:%M")
                                    picks.append(f"🕐 {orario} {home} vs {away} - UNDER 4.5 @ {q}")
                            except: pass
            if len(picks)>=10: break
        if not picks: return f"Oggi 0 partite con UNDER 4.5 <1.20 {OGGI}"
        return f"⬇️ UNDER 4.5 SOTTO 1.20 - {OGGI}\n\n" + "\n".join(picks)
    except Exception as e: return f"Errore under: {e}"

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
                    msg=upd.get("message",{})
                    txt=msg.get("text","").lower().split("@")[0].strip()
                    from_chat=msg.get("chat",{}).get("id")
                    if "spegni" in txt or txt.startswith("/pausa") or txt in ["pausa","stop","🔴 spegni"]:
                        is_paused=True; tg("🛑 PAUSA",from_chat,con_tastiera=True)
                    elif "accendi" in txt or txt.startswith("/riprendi") or txt in ["/on","/start","on","🟢 accendi"]:
                        is_paused=False; tg("✅ RIPRESO",from_chat,con_tastiera=True)
                    elif "status" in txt:
                        ora=datetime.now(ITALY).strftime('%H:%M')
                        st="PAUSA" if is_paused else "ATTIVO"
                        tg(f"📊 {st} | {ora} | Coda tripla:{len(tripla_coda)}",from_chat,con_tastiera=True)
                    elif "bolla" in txt or "bola" in txt:
                        tg("⏳ Creo bolla...",from_chat); tg(crea_bolla_15(),from_chat,con_tastiera=True)
                    elif "under" in txt:
                        tg("⏳ Cerco UNDER 4.5 <1.20...",from_chat); tg(crea_bolla_under(),from_chat,con_tastiera=True)
        except: pass
        time.sleep(30 if is_paused else 2)
threading.Thread(target=poll_commands,daemon=True).start()

def get_flag(p):
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸","Australia":"🇦🇺","Japan":"🇯🇵","South Korea":"🇰🇷"}
    return m.get(p,f"[{p}]")

while True:
    try:
        if is_paused:
            time.sleep(60); continue
        now=datetime.now(ITALY)
        if 0<=now.hour<10:
            if now.hour==0:
                av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
            time.sleep(600); continue
        live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live=="LIMIT":
            time.sleep(3600); continue
        if not live:
            time.sleep(180); continue
        if time.time()-ultimo_invio_tripla>=3600 and len(tripla_coda)>=2:
            txt=f"🔥🔥🔥 TRIPLA ORARIA {now.strftime('%H:%M')} 🔥🔥🔥\n\n"
            for p in tripla_coda[:3]: txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
            tg(txt); tripla_coda=tripla_coda[3:]; ultimo_invio_tripla=time.time()
        for g in live:
            fid=g["fixture"]["id"]; st=g["fixture"]["status"]["short"]; m=g["fixture"]["status"]["elapsed"]
            if m is None: continue
            home=g['teams']['home']['name']; away=g['teams']['away']['name']
            gh=g['goals']['home'] or 0; ga=g['goals']['away'] or 0
            paese=g['league']['country']; lega=g['league']['name']
            flag=get_flag(paese); pref=f"{flag} {paese.upper()} - {lega}"
            def tiri():
                try:
                    d=cache.get(fid)
                    if d and time.time()-d.get('time',0) < 180: return d.get('sot',0)
                    s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if s and len(s)>=2:
                        sot=0
                        for team_stat in s:
                            for stt in team_stat['statistics']:
                                t=stt.get('type','')
                                if 'Shots on Goal' in t or 'Shots on Target' in t or t=='Shots on Goal':
                                    try: sot+=int(str(stt.get('value') or 0))
                                    except: pass
                        cache[fid]={'sot':sot,'time':time.time()}; time.sleep(0.5); return sot
                    return d.get('sot',0) if d else 0
                except: return 0
            if st=="HT" and fid not in pre1:
                so=tiri()
                if so>=3:
                    tg(f"⏸️ FINE 1T {pref} | Tiri:{so} | {home} {gh}-{ga} {away}"); pre1.add(fid)
            if 46 <= (m or 0) <= 69 and fid not in pre:
                so=tiri()
                if so>=5:
                    tg(f"🔔 PREPARATI {m}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | al 70' GIOCALO"); pre.add(fid)
            if 70 <= (m or 0) <= 92 and fid not in av_s:
                so=tiri()
                if so>=4:
                    sq=home if gh<=ga else away
                    tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}")
                    av_s.add(fid); av_g[fid]=gh+ga
                    if not any(x['fid']==fid for x in tripla_coda):
                        tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':m,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})
        for g in live:
            fid=g["fixture"]["id"]
            if fid in av_g:
                tot=(g["goals"]["home"] or 0)+(g["goals"]["away"] or 0)
                if tot>av_g[fid]:
                    flag=get_flag(g['league']['country'])
                    tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                    del av_g[fid]
        time.sleep(180)
    except: time.sleep(15)
