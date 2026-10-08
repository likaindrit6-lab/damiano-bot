import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0

try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except:
    pass

app=Flask(__name__)
@app.route('/')
def home():
    return f"BOT OK - {datetime.now(ITALY).strftime('%H:%M')}",200

def run_flask():
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BOLLA"],["STATUS"]],"resize_keyboard":True})

def tg(m,cid=None,kb=False):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        p={"chat_id":cid if cid else CHAT_ID,"text":m,"parse_mode":"HTML"}
        if kb:
            p["reply_markup"]=TASTIERA
        requests.post(url,json=p,timeout=20)
    except:
        pass

def api_get(u):
    try:
        r=requests.get(u,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=25)
        if r.status_code==429:
            return "LIMIT"
        return r.json().get("response",[])
    except:
        return []

def crea_bolla_15():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures:
            return f"Nessuna partita oggi {OGGI}"
        picks=[]
        quota_tot=1.0
        BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly","Amateur"]
        for p in sorted(fixtures,key=lambda x:x["fixture"]["timestamp"]):
            if len(picks)>=20:
                break
            if any(b.lower() in p["league"]["name"].lower() for b in BAN):
                continue
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt<datetime.now(ITALY):
                continue
            home=p["teams"]["home"]["name"]
            away=p["teams"]["away"]["name"]
            paese=p["league"]["country"]
            lega=p["league"]["name"]
            orario=dt.strftime("%H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"):
                continue
            try:
                over=None
                for bet in odds[0]["bookmakers"][0]["bets"]:
                    if "Over/Under" in bet["name"]:
                        for v in bet["values"]:
                            if "Over 0.5" in v["value"]:
                                q=float(v["odd"])
                                if 1.02 <= q <= 1.25:
                                    over=q
                                    break
                        if over:
                            break
                if not over:
                    continue
                quota_tot=round(quota_tot*over,2)
                picks.append(f"{orario} - {paese} - {lega}\n{home} vs {away}\n-> Over 0.5 @ {over}")
            except:
                continue
        if len(picks)<10:
            return f"Trovate solo {len(picks)} Over 0.5 - quota {quota_tot:.2f}"
        return f"BOLLA OVER 0.5 - 20 PARTITE - Quota {quota_tot:.2f}\n\n" + "\n\n".join(picks) + f"\n\nTOT {quota_tot:.2f}"
    except Exception as e:
        return f"Errore: {e}"

def poll_commands():
    global is_paused,last_update_id
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25",timeout=30).json()
            if r.get("ok"):
                for u in r.get("result",[]):
                    last_update_id=u["update_id"]
                    txt=u.get("message",{}).get("text","").lower()
                    chat=u.get("message",{}).get("chat",{}).get("id")
                    if "spegni" in txt:
                        is_paused=True
                        tg("PAUSA",chat,True)
                    elif "accendi" in txt or txt in ["/start","on"]:
                        is_paused=False
                        tg("ATTIVO",chat,True)
                    elif "bolla" in txt:
                        tg("Creo bolla Over 0.5...",chat)
                        tg(crea_bolla_15(),chat,True)
                    elif "status" in txt:
                        tg(f"{'PAUSA' if is_paused else 'ATTIVO'} {datetime.now(ITALY).strftime('%H:%M')}",chat,True)
        except:
            pass
        time.sleep(2)

threading.Thread(target=poll_commands,daemon=True).start()
print("BOT AVVIATO FIX INDENT")

while True:
    try:
        if is_paused:
            time.sleep(30)
            continue
        time.sleep(60)
    except:
        time.sleep(10)
