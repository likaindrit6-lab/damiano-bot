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
    return f"BOT OK {datetime.now(ITALY).strftime('%H:%M')}",200

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
    picks=[]
    quota_tot=1.0
    BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly","Amateur","Club Friend"]
    try:
        for gg in range(3):
            if len(picks)>=20:
                break
            giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
            fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
            if not fixtures:
                continue
            for fx in sorted(fixtures,key=lambda x:x["fixture"]["timestamp"]):
                if len(picks)>=20:
                    break
                league_name=fx["league"]["name"].lower()
                if any(b.lower() in league_name for b in BAN):
                    continue
                fid=fx["fixture"]["id"]
                dt=datetime.fromtimestamp(fx["fixture"]["timestamp"],tz=ITALY)
                if dt<datetime.now(ITALY):
                    continue
                home=fx["teams"]["home"]["name"]
                away=fx["teams"]["away"]["name"]
                paese=fx["league"]["country"]
                lega=fx["league"]["name"]
                orario=dt.strftime("%H:%M")
                odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                if not odds or odds=="LIMIT":
                    continue
                if not odds[0].get("bookmakers"):
                    continue
                bets=odds[0]["bookmakers"][0].get("bets",[])
                over=None
                for bet in bets:
                    if "Over/Under" not in bet["name"]:
                        continue
                    for v in bet.get("values",[]):
                        if "Over 0.5" in v.get("value",""):
                            try:
                                q=float(v.get("odd",0))
                            except:
                                continue
                            if 1.01 <= q <= 1.35:
                                over=q
                                break
                    if over:
                        break
                if not over:
                    continue
                quota_tot=round(quota_tot*over,2)
                picks.append(f"{orario} {giorno[5:10]} {paese} {lega} {home} vs {away} -> Over 0.5 @ {over}")
        if len(picks)<5:
            return f"Trovate solo {len(picks)} partite adesso"
        txt=f"BOLLA OVER 0.5 - {len(picks)} PARTITE - Quota {quota_tot:.2f}\n\n"
        txt+="\n\n".join(picks)
        txt+=f"\n\nTOT {quota_tot:.2f}"
        return txt
    except Exception as e:
        return f"Errore bolla: {e}"

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
                    elif "accendi" in txt or "/start" in txt:
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
tg("BOT RIPARTITO - FIX DEFINITIVO",kb=True)
print("BOT COMPLETO AVVIATO")

while True:
    time.sleep(60)
