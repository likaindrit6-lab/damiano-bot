import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g={}; av_s=set(); pre=set(); pre1=set(); cache={}
tripla_coda=[]; ultimo_invio_tripla=time.time()

try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V28 FINALE - {s}",200

def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({
    "keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BLASONATE","🔥 15 SICURE"],["⬇️ UNDER","📊 TOKEN"]],
    "resize_keyboard":True,"is_persistent":True
})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
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

def get_token_status():
    try:
        r=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10)
        data=r.json()["response"]; req=data["requests"]
        cur=req.get("current",0); lim=req.get("limit_day",7500)
        return f"📊 TOKEN {cur}/{lim} Rimasti:{lim-cur}"
    except Exception as e: return f"Errore token: {e}"

def get_flag(p):
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷"}
    return m.get(p,"🏳️")

def is_ok_league(league, country):
    ln=(league+" "+country).lower()
    if any(x in ln for x in ["women","female","u19","u21","u23","u20","u18","reserve","youth"]):
        return False
    return True

def is_blasonata(league, country):
    if not is_ok_league(league, country): return False
    ln=league.lower(); c=country
    if c=="Italy" and ("serie a" in ln or "serie b" in ln): return True
    if c=="England" and ("premier league" in ln or "championship" in ln): return True
    if c=="Spain" and ("laliga" in ln or "la liga" in ln or "segunda" in ln): return True
    if c=="Germany" and "bundesliga" in ln: return True
    if c=="France" and ("ligue 1" in ln or "ligue 2" in ln): return True
    if c=="Portugal" and "primeira" in ln: return True
    if c=="Netherlands" and "eredivisie" in ln: return True
    return False

def crea_bolla(tipo="blasonate"):
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if tipo=="blasonate":
            fixtures=[f for f in fixtures if is_blasonata(f['league']['name'], f['league']['country'])]
        else:
            fixtures=[f for f in fixtures if is_ok_league(f['league']['name'], f['league']['country'])]
        if not fixtures: return f"Nessuna partita {tipo} oggi {OGGI}"
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        candidati=[]
        for p in fixtures:
            if len(candidati)>=70: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            orario=dt.strftime("%H:%M")
            flag=get_flag(paese)
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            try:
                best=None
                for book in odds[0]["bookmakers"]:
                    for bet in book["bets"]:
                        if any(k in bet["name"].lower() for k in ["double chance","over/under","multigoal"]):
                            for v in bet["values"]:
                                try:
                                    q=float(v["odd"])
                                    if 1.05 <= q <= 1.28 and (best is None or q < best["q"]):
                                        best={"m":bet["name"],"e":v["value"],"q":q}
                                except: continue
                if not best: continue
                qenc_bet=urllib.parse.quote_plus(f"{home} {away} site:bet365.it")
                qenc_planet=urllib.parse.quote_plus(f"{home} {away} site:planetwin365.it")
                link_bet365=f"https://www.google.com/search?q={qenc_bet}&btnI=1"
                link_planet=f"https://www.google.com/search?q={qenc_planet}&btnI=1"
                link_stats=f"https://www.flashscore.it/search/?q={urllib.parse.quote_plus(home+' '+away)}"
                if "Double" in best["m"]:
                    txt=f"DOPPIA {best['e'].replace('Home/Draw','1X').replace('Draw/Away','X2').replace('Home/Away','12')}"
                elif "Over 0.5" in best["e"]:
                    txt=f"OVER 0.5"
                else:
                    txt=f"MULTIGOL {best['e']}"
                prob=int((1/best["q"])*100)
                riga=f"{flag} <b>{paese.upper()}</b> | 🕐 {orario} | 🏆 {lega}\n{home} vs {away}\n👉 {txt} @ {best['q']} ({prob}%)\n<a href='{link_bet365}'>BET365</a> | <a href='{link_planet}'>PLANETWIN365</a> | <a href='{link_stats}'>STATS</a>"
                candidati.append({"q":best["q"],"txt":riga})
            except: continue
        if not candidati: return f"0 partite {tipo} 85%+ oggi"
        candidati=sorted(candidati,key=lambda x:x["q"])
        picks=candidati[:12 if tipo=="blasonate" else 15]
        quota_tot=1.0
        for p in picks: quota_tot*=p["q"]
        titolo="BLASONATE A/B" if tipo=="blasonate" else "15 SICURE 85%"
        return f"🔥 {titolo} - {OGGI} - {quota_tot:.2f} 🔥\n\n"+"\n\n".join([p["txt"] for p in picks])+f"\n\n💰 TOT {quota_tot:.2f}"
    except Exception as e: return f"Errore: {e}"

def crea_bolla_under():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        picks=[]
        for p in fixtures:
            if not is_ok_league(p['league']['name'], p['league']['country']): continue
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            for bet in odds[0]["bookmakers"][0]["bets"]:
                if "Over/Under" in bet["name"] and "4.5" in str(bet["values"]):
                    for v in bet["values"]:
                        if "Under 4.5" in v["value"]:
                            try:
                                q=float(v["odd"])
                                if q < 1.20:
                                    flag=get_flag(p['league']['country'])
                                    qenc_bet=urllib.parse.quote_plus(f"{home} {away} site:bet365.it")
                                    qenc_planet=urllib.parse.quote_plus(f"{home} {away} site:planetwin365.it")
                                    link_bet365=f"https://www.google.com/search?q={qenc_bet}&btnI=1"
                                    link_planet=f"https://www.google.com/search?q={qenc_planet}&btnI=1"
                                    picks.append(f"{flag} {home} vs {away} - UNDER 4.5 @ {q}\n<a href='{link_bet365}'>BET365</a> | <a href='{link_planet}'>PLANETWIN365</a>")
                            except: pass
            if len(picks)>=10: break
        if not picks: return f"0 UNDER oggi {OGGI}"
        return f"⬇️ UNDER 4.5 - {OGGI}\n\n" + "\n\n".join(picks)
    except Exception as e: return f"Errore under: {e}"

def poll_commands():
    global is_paused,last_update_id
    while True:
        try:
            base=f"https://api.telegram.org/bot{BOT_TOKEN}"
            r=requests.get(base+f"/getUpdates?offset={last_update_id+1}&timeout=25",timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    txt=upd.get("message",{}).get("text","").lower()
                    from_chat=upd.get("message",{}).get("chat",{}).get("id")
                    if "spegni" in txt:
                        is_paused=True; tg("🛑 PAUSA",from_chat,con_tastiera=True)
                    elif "accendi" in txt or "/start" in txt:
                        is_paused=False; tg("✅ V28 PRONTO - BLASONATE + 15 SICURE",from_chat,con_tastiera=True)
                    elif "token" in txt:
                        tg(get_token_status(),from_chat,con_tastiera=True)
                    elif "blasonate" in txt:
                        tg("⏳ Blasonate A/B...",from_chat); tg(crea_bolla("blasonate"),from_chat,con_tastiera=True)
                    elif "15" in txt or "sicure" in txt:
                        tg("⏳ 15 sicure 85%...",from_chat); tg(crea_bolla("sicure"),from_chat,con_tastiera=True)
                    elif "bolla" in txt:
                        tg("⏳ Blasonate...",from_chat); tg(crea_bolla("blasonate"),from_chat,con_tastiera=True)
                    elif "under" in txt:
                        tg("⏳ UNDER...",from_chat); tg(crea_bolla_under(),from_chat,con_tastiera=True)
        except: pass
        time.sleep(2)
threading.Thread(target=poll_commands,daemon=True).start()

while True:
    try:
        if is_paused: time.sleep(60); continue
        now=datetime.now(ITALY)
        if 0<=now.hour<10:
            if now.hour==0:
                av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear();tripla_coda.clear()
            time.sleep(600); continue
        live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live=="LIMIT": time.sleep(3600); continue
        if not live: time.sleep(180); continue
        time.sleep(180)
    except: time.sleep(15)
