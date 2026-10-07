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

try:
    base=f"https://api.telegram.org/bot{BOT_TOKEN}"
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA" if is_paused else "ATTIVO"
    return f"BOT V34 UNDER 4.5 STABILE - {s}",200

def run_flask():
    try:
        from waitress import serve
        p=int(os.environ.get("PORT",10000))
        serve(app,host='0.0.0.0',port=p)
    except:
        app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
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
            if len(risultati)>=30: break
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
            trovato=False
            for book in odds[0]["bookmakers"]:
                if trovato: break
                for bet in book.get("bets",[]):
                    if "OVER/UNDER" not in bet["name"].upper() and "TOTAL" not in bet["name"].upper(): continue
                    for v in bet.get("values",[]):
                        if "under 4.5" in v["value"].lower():
                            try:
                                q=float(v["odd"])
                                if 1.03 <= q <= 1.20: # SOTTO 1.20 COME VUOI TU
                                    risultati.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 UNDER 4.5 @ {q}\n<a href='{link_bet365}'>BET365</a>")
                                    trovato=True
                                    break
                            except: pass
                    if trovato: break
            time.sleep(0.2)
        if not risultati: return f"Nessuna Under 4.5 sotto 1.20 nelle 24H"
        return f"⚽ UNDER 4.5 SOTTO 1.20 - 24H ({len(risultati)})\n\n" + "\n\n".join(risultati)
    except Exception as e:
        return f"Errore under: {e}"

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
            book_to_use=odds[0]["bookmakers"][0]
            try:
                best=None
                for bet in book_to_use["bets"]:
                    if "OVER/UNDER" in bet["name"].upper() or "1X2" in bet["name"].upper() or "DOUBLE" in bet["name"].upper():
                        for v in bet["values"]:
                            try:
                                q=float(v["odd"])
                                if 1.15 <= q <= 1.40 and (best is None or q>best["q"]):
                                    best={"e":v["value"],"q":q}
                            except: continue
                if not best: continue
                if quota_tot*best["q"]>3.60: continue
                quota_tot*=best["q"]
                picks.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 {best['e']} @ {best['q']}\n<a href='{link_bet365}'>BET365</a>")
            except: continue
        if len(picks)<4: return f"Poche partite, trovate {len(picks)} quota {quota_tot:.2f}"
        return f"🔥 BOLLA {OGGI} - {quota_tot:.2f}\n\n"+"\n\n".join(picks)
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
                    if "spegni" in txt or "pausa" in txt:
                        is_paused=True; tg("🛑 PAUSA",from_chat,con_tastiera=True)
                    elif "accendi" in txt or "/on" in txt or "/start" in txt:
                        is_paused=False; tg("✅ RIPRESO",from_chat,con_tastiera=True)
                    elif "status" in txt:
                        ora=datetime.now(ITALY).strftime('%H:%M'); st="PAUSA" if is_paused else "ATTIVO"
                        tg(f"📊 {st} | {ora}",from_chat,con_tastiera=True)
                    elif "under" in txt:
                        tg("⏳ Cerco Under 4.5 sotto 1.20 - 24H...",from_chat)
                        tg(lista_under_35(),from_chat,con_tastiera=True)
                    elif "bolla" in txt or "bola" in txt:
                        tg("⏳ Creo bolla...",
