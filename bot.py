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

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V18 FIX - {s} - {datetime.now(ITALY).strftime('%H:%M')}",200

TASTIERA_JSON=json.dumps({
    "keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"]],
    "resize_keyboard":True,"is_persistent":True
})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        if not BOT_TOKEN or not cid:
            return
        base=f"https://api.telegram.org/bot{BOT_TOKEN}"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera:
            payload["reply_markup"]=TASTIERA_JSON
        requests.post(base+"/sendMessage",json=payload,timeout=25)
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
    try:
        picks=[]
        quota_tot=1.0
        BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly","Amateur","Club Friend"]
        for gg in range(3):
            if len(picks)>=20:
                break
            giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
            fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
            if not fixtures:
                continue
            fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
            for p in fixtures:
                if len(picks)>=20:
                    break
                if any(b.lower() in p["league"]["name"].lower() for b in BAN):
                    continue
                fid=p["fixture"]["id"]
                dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
                if dt < datetime.now(ITALY):
                    continue
                home=p['teams']['home']['name']
                away=p['teams']['away']['name']
                paese=p['league']['country']
                lega=p['league']['name']
                orario=dt.strftime("%H:%M")
                qenc=urllib.parse.quote_plus(home+" "+away)
                qenc_bet=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
                link_bet365=f"https://www.google.com/search?q={qenc_bet}&btnI=1"
                link_stats=f"https://www.flashscore.it/search/?q={qenc}"
                odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                if not odds or odds=="LIMIT":
                    continue
                if not odds[0].get("bookmakers"):
                    continue
                try:
                    over=None
                    for bet in odds[0]["bookmakers"][0]["bets"]:
                        if "Over/Under" not in bet["name"]:
                            continue
                        for v in bet["values"]:
                            if "Over 0.5" in v["value"]:
                                try:
                                    q=float(v["odd"])
                                    if 1.01 <= q <= 1.35:
                                        over=q
                                        break
                                except:
                                    continue
                        if over:
                            break
                    if not over:
                        continue
                    quota_tot=round(quota_tot*over,2)
                    picks.append(f"🕐 {orario} {giorno[5:10]} - {paese} - {lega}\n{home} vs {away}\n👉 Over 0.5 @ {over}\n<a href='{link_bet365}'>BET365</a> | <a href='{link_stats}'>STATS</a>")
                except:
                    continue
        if len(picks)<5:
            return f"Oggi poche partite, trovate {len(picks)}"
        return f"🔥 BOLLA OVER 0.5 - {len(picks)} PARTITE - Quota {quota_tot:.2f} 🔥\n\n"+"\n\n".join(picks)+f"\n\n💰 TOT {quota_tot:.2f}"
    except Exception as e:
        return f"Errore bolla: {e}"

def poll_commands():
    global is_paused,last_update_id
    try:
        base_del=f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        if BOT_TOKEN:
            requests.get(base_del,timeout=10)
    except:
        pass
    while True:
        try:
            if not BOT_TOKEN:
                time.sleep(60)
                continue
            base=f"https://api.telegram.org/bot{BOT_TOKEN}"
            url=base+f"/getUpdates?offset={last_update_id+1}&timeout=25"
            r=requests.get(url,timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    msg=upd.get("message",{})
                    txt_raw=msg.get("text","")
                    txt=txt_raw.lower().split("@")[0].strip()
                    from_chat=msg.get("chat",{}).get("id")
                    if "spegni" in txt or "🔴" in txt_raw:
                        is_paused=True
                        tg("🛑 PAUSA",from_chat,con_tastiera=True)
                    elif "accendi" in txt or "/start" in txt or "🟢" in txt_raw:
                        is_paused=False
                        tg("✅ RIPRESO",from_chat,con_tastiera=True)
                    elif "status" in txt:
                        tg(f"📊 {'PAUSA' if is_paused else 'ATTIVO'} | {datetime.now(ITALY).strftime('%H:%M')}",from_chat,con_tastiera=True)
                    elif "bolla" in txt:
                        tg("⏳ Creo bolla 20...",from_chat)
                        tg(crea_bolla_15(),from_chat,con_tastiera=True)
        except:
            pass
        time.sleep(2)

def get_stat(a,n):
    for s in a:
        if s.get('type')==n:
            try:
                return int(str(s.get('value') or 0).replace('%','').strip() or 0)
            except:
                return 0
    return 0

def get_flag(p):
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷"}
    return m.get(p,f"[{p}]")

def bot_live_loop():
    global av_g,av_s,pre,pre1,cache,tripla_coda,ultimo_invio_tripla
    tg("BOT V18 FIX - LIVE + BOLLA 20 ✅",con_tastiera=True)
    print("BOT LIVE AVVIATO")
    while True:
        try:
            if is_paused:
                time.sleep(60)
                continue
            now=datetime.now(ITALY)
            if 2 <= now.hour < 6:
                time.sleep(300)
                continue
            if now.hour==0 and now.minute<5:
                av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
            live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if live=="LIMIT":
                time.sleep(3600)
                continue
            if not live:
                time.sleep(60)
                continue
            if time.time()-ultimo_invio_tripla>=3600 and len(tripla_coda)>=2:
                txt=f"🔥🔥🔥 TRIPLA ORARIA {now.strftime('%H:%M')} 🔥🔥🔥\n\n"
                for p in tripla_coda[:3]:
                    txt+=f"{p['flag']} {p['pref']} | {p['min']}' | Tiri:{p['sot']} | {p['home']} {p['gh']}-{p['ga']} {p['away']}\n"
                tg(txt)
                tripla_coda=tripla_coda[3:]
                ultimo_invio_tripla=time.time()
            for g in live:
                fid=g["fixture"]["id"]
                st=g["fixture"]["status"]["short"]
                m=g["fixture"]["status"]["elapsed"]
                if m is None or fid in av_s:
                    continue
                home=g['teams']['home']['name']
                away=g['teams']['away']['name']
                gh=g['goals']['home']
                ga=g['goals']['away']
                paese=g['league']['country']
                lega=g['league']['name']
                flag=get_flag(paese)
                pref=f"{flag} {paese.upper()} - {lega}"
                def tiri():
                    d=cache.get(fid)
                    if not d or time.time()-d.get('time',0)>180:
                        s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                        if s and len(s)>=2:
                            sot=get_stat(s[0]['statistics'],'Shots on Goal')+get_stat(s[1]['statistics'],'Shots on Goal')
                            cache[fid]={'sot':sot,'time':time.time()}
                            time.sleep(0.4)
                            return sot
                        return d.get('sot',0) if d else 0
                    return d.get('sot',0)
                if st=="HT" and fid not in pre1:
                    so=tiri()
                    if so>=3:
                        tg(f"⏸️ FINE 1T {pref} | Tiri:{so} | {home} {gh}-{ga} {away}")
                        pre1.add(fid)
                if 46<=(m or 0)<=69 and fid not in pre:
                    so=tiri()
                    if so>=5:
                        tg(f"🔔 PREPARATI {m}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT")
                        pre.add(fid)
                if 65<=(m or 0)<=92:
                    so=tiri()
                    if so>=4 and fid not in av_s:
                        sq=home if gh<=ga else away
                        tg(f"🔥 GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}")
                        av_s.add(fid)
                        av_g[fid]=gh+ga
                        if not any(x['fid']==fid for x in tripla_coda):
                            tripla_coda.append({'fid':fid,'flag':flag,'pref':f"{paese} - {lega}",'min':m,'sot':so,'home':home,'away':away,'gh':gh,'ga':ga})
            for g in live:
                fid=g["fixture"]["id"]
                if fid in av_g:
                    tot=g["goals"]["home"]+g["goals"]["away"]
                    if tot>av_g[fid]:
                        flag=get_flag(g['league']['country'])
                        tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                        del av_g[fid]
            time.sleep(60)
        except Exception as e:
            print(f"ERR: {e}")
            time.sleep(15)

threading.Thread(target=poll_commands,daemon=True).start()
threading.Thread(target=bot_live_loop,daemon=True).start()

if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    print(f"FLASK AVVIATO SU {port}")
    app.run(host='0.0.0.0',port=port)
