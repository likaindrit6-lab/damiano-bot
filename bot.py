import os,time,requests,threading,random
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
bolla_attiva=[]
bolla_attiva_info={}
bolla_creata_ora=0
av_g,av_s,pre,pre1,cache={},set(),set(),set(),{}
tripla_coda=[]
ultimo_invio_tripla=time.time()

try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    stato=f" | Bolla: {len(bolla_attiva)} q{bolla_attiva_info.get('quota',0):.2f}" if bolla_attiva else " | Bolla: nessuna"
    return f"BOT V10.4 ITA FINALE 1.60 - {'PAUSA' if is_paused else 'ATTIVO'}{stato}",200

def run_flask():
    from waitress import serve
    serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

def tg(m,chat_id=None):
    try:
        cid=chat_id if chat_id else CHAT_ID
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":cid,"text":m,"parse_mode":"HTML"},timeout=25)
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
            try: return int(str(s.get('value') or 0).replace('%','').strip() or 0)
            except: return 0
    return 0

def get_flag(p):
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸"}
    return m.get(p,f"[{p}]")

def get_tiri(fid):
    try:
        d=cache.get(fid)
        if d and time.time()-d.get('time',0) <= 180: return d.get('sot',0)
        s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
        if s and len(s)>=2:
            sot=get_stat(s[0]['statistics'],'Shots on Goal')+get_stat(s[1]['statistics'],'Shots on Goal')
            cache[fid]={'sot':sot,'time':time.time()}; time.sleep(0.4); return sot
        return d.get('sot',0) if d else 0
    except: return 0

def crea_nuova_bolla(chat_id=None):
    global bolla_attiva,bolla_attiva_info,bolla_creata_ora
    try:
        oggi=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
        if fixtures=="LIMIT": return
        candidati=[]; now_utc=datetime.now(timezone.utc)
        for f in fixtures:
            if f["fixture"]["status"]["short"]!="NS": continue
            try:
                kickoff=datetime.fromisoformat(f["fixture"]["date"].replace("Z","+00:00"))
                diff=(kickoff-now_utc).total_seconds()/60
                if 15<=diff<=300: candidati.append(f)
            except: continue
        if len(candidati)<4:
            domani=(datetime.now(ITALY)+timedelta(days=1)).strftime("%Y-%m-%d")
            f2=api_get(f"https://v3.football.api-sports.io/fixtures?date={domani}")
            if f2!="LIMIT":
                for f in f2:
                    if f["fixture"]["status"]["short"]=="NS": candidati.append(f)
        if len(candidati)<4: return
        random.shuffle(candidati)
        bolla_attiva=[]; quota_tot=1
        for f in candidati:
            if quota_tot>=1.80 or len(bolla_attiva)>=5: break
            qx2=1.18
            flag=get_flag(f["league"]["country"])
            home=f["teams"]["home"]["name"]; away=f["teams"]["away"]["name"]
            orario=f["fixture"]["date"][11:16]; lega=f["league"]["name"]
            bolla_attiva.append({"fid":f["fixture"]["id"],"home":home,"away":away,"flag":flag,"orario":orario,"lega":lega,"quota":qx2,"esito":None})
            quota_tot*=qx2
        txt=f"🎫 <b>BOLLA X2 85% - QUOTA {quota_tot:.2f}</b> 🎫\nStake 1.60U\n\n"
        for i,p in enumerate(bolla_attiva,1):
            txt+=f"{i}. {p['flag']} {p['home']} - {p['away']} -> X2 @{p['quota']} ({p['lega']} {p['orario']})\n"
        txt+=f"\n💰 TOT {quota_tot:.2f} - Ti avviso io VINTO/PERSO finale"
        tg(txt,chat_id); bolla_creata_ora=time.time(); bolla_attiva_info={"quota":quota_tot}
    except: pass

def check_bolla_finale():
    global bolla_attiva
    if not bolla_attiva: return
    try:
        for p in bolla_attiva:
            if p["esito"] is None:
                res=api_get(f"https://v3.football.api-sports.io/fixtures?id={p['fid']}")
                if res and res!="LIMIT" and len(res)>0:
                    st=res[0]["fixture"]["status"]["short"]
                    if st in ["FT","AET","PEN"]:
                        gh=res[0]["goals"]["home"]; ga=res[0]["goals"]["away"]
                        p["esito"]="WIN" if ga>=gh else "LOSE"
                        p["ris"]=f"{gh}-{ga}"
        finite=sum(1 for x in bolla_attiva if x["esito"] is not None)
        if finite==len(bolla_attiva) and finite>0:
            vinte=sum(1 for x in bolla_attiva if x["esito"]=="WIN")
            det="\n".join([f"{'✅' if x['esito']=='WIN' else '❌'} {x['flag']} {x['home']} {x.get('ris','')} {x['away']} X2" for x in bolla_attiva])
            if vinte==len(bolla_attiva):
                tg(f"🎉🎉🎉 CONGRATULAZIONI! BOLLA VINTA {vinte}/{len(bolla_attiva)}! 🎉🎉🎉\n\n{det}\n💰 Quota {bolla_attiva_info.get('quota',0):.2f} VINTA!")
            else:
                tg(f"❌ BOLLA PERSA {vinte}/{len(bolla_attiva)}\n\n{det}")
            bolla_attiva.clear()
    except: pass

def poll_commands():
    global is_paused,last_update_id
    while True:
        try:
            url=f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25"
            r=requests.get(url,timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    txt=upd.get("message",{}).get("text","").lower().split("@")[0].strip()
                    from_chat=upd.get("message",{}).get("chat",{}).get("id")
                    if txt.startswith("/pausa"): is_paused=True; tg("🛑 PAUSA",from_chat)
                    elif txt.startswith("/riprendi") or txt in ["riprendi","/on","/start"]: is_paused=False; tg("✅ RIPRESO - Segnali+Tripla+Bolla ON",from_chat)
                    elif txt.startswith("/status"): tg(f"📊 {'PAUSA' if is_paused else 'ATTIVO'} | Tripla:{len(tripla_coda)}/3 | Bolla:{len(bolla_attiva)}",from_chat)
                    elif txt.startswith("/schedina") or txt.startswith("/bolla"):
                        if bolla_attiva:
                            t=f"🎫 BOLLA ATTIVA q{bolla_attiva_info.get('quota',0):.2f}\n"
                            for p in bolla_attiva: t+=f"{p['flag']} {p['home']}-{p['away']} X2\n"
                            tg(t,from_chat)
                        else: crea_nuova_bolla(from_chat)
        except: pass
        time.sleep(30 if is_paused else 2)
threading.Thread(target=poll_commands,daemon=True).start()
print("BOT V10.4 ITA - ATTIVO",flush=True)

while True:
    try:
        if is_paused: time.sleep(60); continue
        now=datetime.now(ITALY)
        if 0<=now.hour<10:
            if now.hour==0: av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
            time.sleep(600); continue
        if bolla_attiva and int(time.time())%180==0: check_bolla_finale()
        live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live=="LIMIT": time.sleep(3600); continue
        if not live: time.sleep(60); continue
        if time.time()-ultimo_invio_tripla>=3600 and len(tripla_coda)>=2:
            txt=f"🔥🔥🔥 TRIPLA ORARIA {now.strftime('%H:%M')} 🔥🔥🔥\n\n"; q=1
            for p in tripla_coda[:3]: txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"; q*=1.45
            txt+=f"\n💰 QUOTA ~{q:.2f}"; tg(txt); tripla_coda=tripla_coda[3:]; ultimo_invio_tripla=time.time()
        for g in live:
            fid=g["fixture"]["id"]; m=g["fixture"]["status"]["elapsed"]
            if m is None or fid in av_s: continue
            home=g['teams']['home']['name']; away=g['teams']['away']['name']; gh=g['goals']['home']; ga=g['goals']['away']
            paese=g['league']['country']; lega=g['league']['name']; flag=get_flag(paese); pref=f"{flag} {paese.upper()} - {lega}"; so=get_tiri(fid)
            if 46<=m<=69 and fid not in pre and so>=5: tg(f"🔔 PREPARATI {m}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT"); pre.add(fid)
            if 65<=m<=92 and so>=4 and fid not in av_s:
                sq=home if gh<=ga else away
                tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}"); av_s.add(fid); av_g[fid]=gh+ga
                if not any(x['fid']==fid for x in tripla_coda): tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':m,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})
        for g in live:
            fid=g["fixture"]["id"]
            if fid in av_g and g["goals"]["home"]+g["goals"]["away"]>av_g[fid]:
                flag=get_flag(g['league']['country']); tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}"); del av_g[fid]
        time.sleep(60)
    except: time.sleep(15)
