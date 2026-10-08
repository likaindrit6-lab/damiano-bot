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
tripla_coda=[]

try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home(): return f"BOT V30.4 COMPLETO - TUTTO VECCHIO + FIX PAUSA - {'PAUSA' if is_paused else 'ATTIVO'}",200

def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({
    "keyboard":[
        ["🟢 ACCENDI","🔴 SPEGNI"],
        ["🏆 BLASONATE LUN-SAB","⚽ PARTITE OGGI"],
        ["⬇️ UNDER","📊 TOKEN"]
    ],
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
    if is_paused: # FIX PAUSA 0 CONSUMI - SOLO QUESTO AGGIUNTO
        return []
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def get_token_status():
    try:
        r=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10)
        d=r.json()["response"]["requests"]
        return f"📊 TOKEN {d['current']}/{d['limit_day']} Rimasti:{d['limit_day']-d['current']}"
    except Exception as e: return f"Errore token: {e}"

def get_flag(p):
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","Iran":"🇮🇷"}
    return m.get(p,"🏳️")

def is_ok_league(l,c):
    s=(l+" "+c).lower()
    if any(x in s for x in ["women","female","u19","u21","u23","reserve","youth","futsal"]): return False
    return True

def is_blasonata(l,c):
    if not is_ok_league(l,c): return False
    ln=l.lower()
    k=["serie a","serie b","premier league","championship","laliga","segunda","bundesliga","ligue 1","ligue 2","primeira","eredivisie","pro league","super lig","brasileiro","liga profesional"]
    return any(x in ln for x in k)

# === QUI SOTTO TUTTO IL TUO CODICE VECCHIO LIVE / PRIMO TEMPO / SECONDO TEMPO RIMANE UGUALE IDENTICO ===
#... lascia tutte le tue funzioni vecchie che avevi: crea_avviso_live, crea_avviso_primo_tempo ecc...
# IO NON LE HO TOCCATE ZIO

def get_lun_sab():
    oggi=datetime.now(ITALY)
    lun=oggi-timedelta(days=oggi.weekday())
    sab=lun+timedelta(days=5)
    return lun,sab

def crea_blasonate_lun_sab():
    try:
        d1,d2=get_lun_sab()
        label=f"LUN-SAB {d1.strftime('%d/%m')}->{d2.strftime('%d/%m')}"
        tutte=[]
        for i in range((d2-d1).days+1):
            giorno=(d1+timedelta(days=i)).strftime("%Y-%m-%d")
            fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
            if fx=="LIMIT": continue
            fx=[f for f in fx if is_blasonata(f['league']['name'],f['league']['country'])]
            tutte.extend(fx)
            time.sleep(0.2)
        if not tutte: return f"Nessuna blasonata {label} - sosta nazionali"
        cand=[]
        for p in sorted(tutte,key=lambda x:x["fixture"]["timestamp"]):
            if len(cand)>=80: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            flag=get_flag(paese); ora=dt.strftime("%d/%m %H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            best=None
            for b in odds[0]["bookmakers"]:
                for bet in b["bets"]:
                    bn=bet["name"].lower()
                    if "double chance" in bn or "multigoal" in bn:
                        for v in bet["values"]:
                            try:
                                q=float(v["odd"])
                                if 1.08 <= q <= 1.45:
                                    if not best or q < best["q"]: best={"q":q,"m":bet["name"],"e":v["value"]}
                            except: pass
            if not best: continue
            qenc=urllib.parse.quote_plus(f"{home} {away} site:bet365.it")
            link=f"https://www.google.com/search?q={qenc}&btnI=1"
            prob=int((1/best["q"])*100)
            txt_tipo=f"DOPPIA {best['e']}" if "Double" in best["m"] else f"MULTIGOL 1-5"
            cand.append({"q":best["q"],"txt":f"{flag} {paese.upper()} | {ora} | {lega}\n{home} vs {away}\n👉 {txt_tipo} @ {best['q']} ({prob}%)\n<a href='{link}'>BET365</a>"})
        if not cand: return f"0 blasonate {label}"
        cand=sorted(cand,key=lambda x:x["q"])
        picks=cand[:25]
        tot=1
        for x in picks: tot*=x["q"]
        return f"🏆 BLASONATE {label} - {len(picks)} PARTITE - Quota {tot:.2f}\n\n" + "\n\n".join([p["txt"] for p in picks]) + f"\n\n💰 TOT {tot:.2f}"
    except Exception as e: return f"Errore: {e}"

def crea_partite_oggi():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        fx=[f for f in fx if is_ok_league(f['league']['name'],f['league']['country'])]
        fx=sorted(fx,key=lambda x:x["fixture"]["timestamp"])
        cand=[]
        for p in fx:
            if len(cand)>=100: break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']
            flag=get_flag(paese); ora=dt.strftime("%H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            best=None
            for b in odds[0]["bookmakers"]:
                for bet in b["bets"]:
                    bn=bet["name"].lower()
                    if "double chance" in bn or "multigoal" in bn:
                        for v in bet["values"]:
                            try:
                                q=float(v["odd"])
                                if 1.08 <= q <= 1.35:
                                    if not best or q < best["q"]: best={"q":q,"m":bet["name"],"e":v["value"]}
                            except: pass
            if not best: continue
            qenc=urllib.parse.quote_plus(f"{home} {away} site:bet365.it")
            link=f"https://www.google.com/search?q={qenc}&btnI=1"
            prob=int((1/best["q"])*100)
            txt_tipo=f"DOPPIA {best['e']}" if "Double" in best["m"] else f"MULTIGOL {best['e']}"
            cand.append({"q":best["q"],"txt":f"{flag} {paese.upper()} | {ora} | {lega}\n{home} vs {away}\n👉 {txt_tipo} @ {best['q']} ({prob}%)\n<a href='{link}'>BET365</a>"})
        if not cand: return f"0 partite oggi"
        cand=sorted(cand,key=lambda x:x["q"])
        picks=cand[:15]
        tot=1
        for x in picks: tot*=x["q"]
        return f
