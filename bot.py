import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_s=set(); av_g={}; cache={}

# Spegni webhook vecchio
try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home(): return "BOT V37 VELOCE OK",200
def run_flask(): app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

def tg(m,cid=None):
    try:
        c=cid if cid else CHAT_ID
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":c,"text":m,"parse_mode":"HTML","disable_web_page_preview":True},timeout=20)
    except: pass

def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=20)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def lista_under_fast():
    try:
        now=datetime.now(ITALY)
        fine=now+timedelta(hours=24)
        OGGI=now.strftime("%Y-%m-%d")
        # Prendo solo OGGI per essere veloce
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures: return "Nessuna partita oggi"
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        risultati=[]
        controllate=0
        for p in fixtures:
            if len(risultati)>=20: break
            if controllate>=25: break # MAX 25 per non bloccare API
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < now: continue
            if dt > fine: continue
            if "U21" in p['league']['name'] or "U19" in p['league']['name'] or "WOMEN" in p['league']['name'].upper(): continue
            controllate+=1
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']; orario=dt.strftime("%H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT":
                time.sleep(1)
                continue
            if not odds[0].get("bookmakers"): continue
            for book in odds[0]["bookmakers"]:
                for bet in book.get("bets",[]):
                    if "OVER/UNDER" not in bet["name"].upper(): continue
                    for v in bet.get("values",[]):
                        if "under 4.5" in v["value"].lower():
                            try:
                                q=float(v["odd"])
                                if q <= 1.20: # SOTTO 1.20 COME VUOI
                                    risultati.append(f"{orario} {paese} {home} vs {away} UNDER 4.5 @ {q}")
                            except: pass
                if risultati and len(risultati)>0 and risultati[-1].startswith(f"{orario}"): break
            time.sleep(0.3)
        if not risultati:
            return f"Ho controllato {controllate} partite - Nessuna Under 4.5 sotto 1.20 (oggi quote basse tipo 1.05)"
        return f"UNDER 4.5 SOTTO 1.20 - {len(risultati)} partite su {controllate} controllate\n\n" + "\n\n".join(risultati)
    except Exception as e:
        return f"Errore: {e}"

def poll():
    global last_update_id
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=20",timeout=30).json()
            if r.get("ok"):
                for u in r.get("result",[]):
                    last_update_id=u["update_id"]
                    txt=u.get("message",{}).get("text","").lower()
                    cid=u.get("message",{}).get("chat",{}).get("id")
                    if "under" in txt:
                        # Lo faccio in thread separato cosi non si blocca
                        def do_under(c=cid):
                            tg("Cerco Under 4.5 sotto 1.20 (20 sec)...",c)
                            res=lista_under_fast()
                            tg(res,c)
                        threading.Thread(target=do_under,daemon=True).start()
                    elif "accendi" in txt or "/start" in txt:
                        tg("Bot acceso - V37 veloce",cid)
        except: pass
        time.sleep(2)

threading.Thread(target=poll,daemon=True).start()

while True:
    time.sleep(60)
