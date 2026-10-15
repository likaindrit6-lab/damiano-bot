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

TOP33 = {
"Italia":135,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,
"Portogallo":94,"Olanda":88,"Belgio":144,"Turchia":203,"Scozia":179,
"Austria":218,"Svizzera":207,"Danimarca":119,"Svezia":113,"Norvegia":103,
"Polonia":106,"Rep Ceca":110,"Croazia":210,"Serbia":286,"Grecia":197,
"Romania":283,"Ungheria":271,"Bulgaria":172,"Slovacchia":334,"Slovenia":373,
"Cipro":318,"Israele":383,"Ucraina":333,"Bielorussia":116,"Irlanda":84,
"Irlanda Nord":410,"Galles":1107,"Islanda":108
}

try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V65 UNIONE - {s}",200

def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({"keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"],["MEDIA SERIE A","MEDIA INGHILTERRA"],["MEDIA SPAGNA","MEDIA EUROPA"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        base=f"https://api.telegram.org/bot{BOT_TOKEN}"
        url=base+"/sendMessage"
        # Spezza messaggi lunghi
        if len(m) > 4000:
            for i in range(0, len(m), 4000):
                payload={"chat_id":cid,"text":m[i:i+4000],"parse_mode":"HTML","disable_web_page_preview":True}
                if con_tastiera and i==0: payload["reply_markup"]=TASTIERA_JSON
                requests.post(url,json=payload,timeout=25)
                time.sleep(1)
        else:
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

def get_stat(a,n):
    for s in a:
        if s.get('type')==n:
            try: v=str(s.get('value') or 0).replace('%','').strip() or 0; return int(v)
            except: return 0
    return 0

def get_flag(p):
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸","Australia":"🇦🇺","Japan":"🇯🇵"}
    return m.get(p,f"[{p}]")

# --- NUOVA FUNZIONE CHE VOLEVI TU: ULTIME 10 + GOL + CORNER ---
def get_stats_completa(team_id):
    # Prende ultime 10 partite e calcola GOL + CORNER veri
    last = api_get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&season=2024")
    gf=0;gs=0;tot_gol=0;win=0;draw=0;lose=0;btts=0
    tot_corner=0
    c=0
    for p in last:
        gh=p["goals"]["home"]; ga=p["goals"]["away"]
        if gh is None: continue
        fid=p["fixture"]["id"]
        hid=p["teams"]["home"]["id"]
        is_home=hid==team_id

        # Gol
        if is_home:
            gf+=gh; gs+=ga
            if gh>ga: win+=1
            elif gh==ga: draw+=1
            else: lose+=1
        else:
            gf+=ga; gs+=gh
            if ga>gh: win+=1
            elif ga==gh: draw+=1
            else: lose+=1
        if gh>0 and ga>0: btts+=1
        tot_gol+=gh+ga

        # Corner - chiama statistics per ogni partita
        stats=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
        if stats and stats!="LIMIT" and len(stats)>=2:
            # Somma corner di entrambe le squadre
            co1=get_stat(stats[0]['statistics'],'Corner Kicks')
            co2=get_stat(stats[1]['statistics'],'Corner Kicks')
            if co1 or co2:
                if is_home:
                    tot_corner+=co1
                else:
                    tot_corner+=co2
            time.sleep(0.3) # per non bruciare API

        c+=1

    if c==0: return None
    return {
        "gf":gf,"gs":gs,
        "media_gol": tot_gol/c,
        "media_corner": tot_corner/c if tot_corner>0 else 0,
        "win":win,"draw":draw,"lose":lose,
        "btts": btts/c,
        "partite":c
    }

def media_league(lid, nome_lega):
    teams = api_get(f"https://v3.football.api-sports.io/teams?league={lid}&season=2024")
    if not teams: return f"Nessuna squadra trovata per {nome_lega}"
    txt = f"📊 {nome_lega.upper()} - STAT ULTIME 10 PARTITE\nGOL + CORNER REALI\n\n"
    for t in teams[:16]: # prime 16 squadre
        tid=t["team"]["id"]; tname=t["team"]["name"]
        st=get_stats_completa(tid)
        if not st: continue
        txt+= f"<b>{tname}</b>\n"
        txt+= f"Gol Med: {round(st['media_gol'],2)} (GF {st['gf']} GS {st['gs']}) | Corner Med: {round(st['media_corner'],1)} | BTTS {int(st['btts']*100)}% | {st['win']}V {st['draw']}P {st['lose']}S\n\n"
        time.sleep(0.2)
    return txt

def media_europa_completa():
    txt = "🌍 MEDIA EUROPA 33 NAZIONI - TOP SQUADRE\n\n"
    for paese, lid in list(TOP33.items())[:10]: # prime 10 nazioni per non esplodere
        teams = api_get(f"https://v3.football.api-sports.io/teams?league={lid}&season=2024")
        if not teams: continue
        txt+= f"--- {paese.upper()} ---\n"
        for t in teams[:3]:
            tid=t["team"]["id"]; tname=t["team"]["name"]
            st=get_stats_completa(tid)
            if not st: continue
            txt+= f"{tname}: Gol {round(st['media_gol'],2)} Corner {round(st['media_corner'],1)}\n"
        txt+="\n"
    return txt

# --- LA TUA BOLLA ORIGINALE ---
def crea_bolla_15():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures: return f"Nessuna partita oggi {OGGI}"
        picks=[]; quota_tot=1.0
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            if len(picks)>=10: break
            if quota_tot>=3.35: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            orario=dt.strftime("%H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue
            try:
                best=None
                for bet in odds[0]["bookmakers"][0]["bets"]:
                    if "First Half" in bet["name"]: continue
                    if "Corners" in bet["name"]: continue
                    if "Cards" in bet["name"]: continue
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
                    if "Home" in m_val: txt="1"
                    elif "Away" in m_val: txt="2"
                    else: txt="X"
                elif "Double Chance" in m_name:
                    mv=m_val.replace("Home/Draw","1X").replace("Draw/Away","X2").replace("Home/Away","12")
                    txt=f"{mv}"
                elif "Both Teams Score" in m_name:
                    txt="GOL SI" if "Yes" in m_val else "GOL NO"
                elif "Over/Under" in m_name:
                    txt=f"{m_val} GOL"
                else:
                    txt=f"{m_name}: {m_val}"
                quota_tot*=best["q"]
                q_finale=best["q"]*1.25
                picks.append(f"🕐 {orario}\n📍 {paese} - {lega}\n{home} vs {away}\n👉 {txt} + Multigol 1-5 @ {q_finale:.2f}")
            except: continue
        if len(picks)<5: return f"Oggi poche partite da 80%, riprova tra 1h. Trovate {len(picks)}"
        return f"🔥 BOLLA {OGGI} - Quota {quota_tot:.2f}\n\n"+"\n\n".join(picks)
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
                    msg=upd.get("message",{})
                    txt=msg.get("text","").lower().split("@")[0].strip()
                    from_chat=msg.get("chat",{}).get("id")
                    if "spegni" in txt or txt in ["🔴 spegni"]:
                        is_paused=True; tg("🛑 PAUSA",from_chat,con_tastiera=True)
                    elif "accendi" in txt or txt in ["🟢 accendi","/start","on"]:
                        is_paused=False; tg("✅ RIPRESO",from_chat,con_tastiera=True)
                    elif "status" in txt:
                        ora=datetime.now(ITALY).strftime('%H:%M'); st="PAUSA" if is_paused else "ATTIVO"
                        tg(f"📊 {st} | {ora}",from_chat,con_tastiera=True)
                    elif "bolla" in txt:
                        tg("⏳ Creo bolla...",from_chat); tg(crea_bolla_15(),from_chat,con_tastiera=True)
                    elif "media serie a" in txt:
                        tg("⏳ Analizzo SERIE A ultime 10 + corner... 2 min",from_chat)
                        tg(media_league(135,"Serie A"),from_chat,con_tastiera=True)
                    elif "media inghilterra" in txt:
                        tg("⏳ Analizzo INGHILTERRA...",from_chat)
                        tg(media_league(39,"Inghilterra"),from_chat,con_tastiera=True)
                    elif "media spagna" in txt:
                        tg("⏳ Analizzo SPAGNA...",from_chat)
                        tg(media_league(140,"Spagna"),from_chat,con_tastiera=True)
                    elif "media europa" in txt:
                        tg("⏳ Analizzo EUROPA 33 nazioni... ci metto 3 min",from_chat)
                        tg(media_europa_completa(),from_chat,con_tastiera=True)
        except: pass
        time.sleep(30 if is_paused else 2)
threading.Thread(target=poll_commands,daemon=True).start()

# --- LOOP LIVE TUO ORIGINALE ---
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
        if time.time()-ultimo_invio_tripla>=3600 and len(tripla_coda)>=2:
            txt=f"🔥🔥🔥 TRIPLA ORARIA {now.strftime('%H:%M')} 🔥🔥🔥\n\n"
            for p in tripla_coda[:3]: txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
            tg(txt); tripla_coda=tripla_coda[3:]; ultimo_invio_tripla=time.time()
        for g in live:
            fid=g["fixture"]["id"]; st=g["fixture"]["status"]["short"]; m=g["fixture"]["status"]["elapsed"]
            if m is None or fid in av_s: continue
            home=g['teams']['home']['name']; away=g['teams']['away']['name']; gh=g['goals']['home']; ga=g['goals']['away']
            paese=g['league']['country']; lega=g['league']['name']; flag=get_flag(paese); pref=f"{flag} {paese.upper()} - {lega}"
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
                    if not any(x['fid']==fid for x in tripla_coda): tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':m,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})
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
