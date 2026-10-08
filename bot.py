import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")

ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
ultimo_gol={}
ultima_schedina_ora=-1
schedina_attiva=[]
schedina_notificata=set()
live_inviate=set()

if BOT_TOKEN:
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except:
        pass

app=Flask(__name__)
@app.route('/')
def home(): return "V38 OK",200
@app.route('/health')
def health(): return "OK",200

TASTIERA=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BLASONATE LUN-DOM","PARTITE OGGI"],["SCHEDINA ORA","TOKEN"]],"resize_keyboard":True})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id or CHAT_ID
        if not BOT_TOKEN or not cid: return
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA
        if len(m)>3800:
            for i in range(0,len(m),3800):
                payload["text"]=m[i:i+3800]
                if i>0: payload.pop("reply_markup",None)
                requests.post(url,json=payload,timeout=15)
                time.sleep(0.3)
        else:
            requests.post(url,json=payload,timeout=15)
    except:
        pass

def api_get(url):
    if is_paused: return []
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=15)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except:
        return []

def crea_blasonate():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if fx=="LIMIT": return "Limite API"
        # LISTA CORTA - una per riga cosi non si spezza
        big=[
            "milan",
            "inter",
            "juventus",
            "napoli",
            "roma",
            "lazio",
            "real madrid",
            "barcelona",
            "psg",
            "bayern",
            "man city",
            "liverpool",
            "arsenal"
        ]
        cand=[]
        for p in fx:
            try:
                home=p['teams']['home']['name']
                away=p['teams']['away']['name']
                txt_low=(home+" "+away).lower()
                ok=False
                for b in big:
                    if b in txt_low:
                        ok=True
                        break
                if not ok: continue
                fid=p["fixture"]["id"]
                odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                if not odds or odds=="LIMIT": continue
                if not odds[0].get("bookmakers"): continue
                doppia=None
                for bk in odds[0]["bookmakers"]:
                    for bet in bk["bets"]:
                        if "double chance" in bet["name"].lower():
                            for v in bet["values"]:
                                vv=v["value"].lower()
                                if "12" in vv: continue
                                if "home/away" in vv: continue
                                try:
                                    q=float(v["odd"])
                                    if 1.10 <= q <= 1.60:
                                        doppia={"q":q,"e":v["value"]}
                                except:
                                    pass
                if not doppia: continue
                # MULTIGOL 1-5 = Under 4.5 su Bet365 = stesso di Planetwin
                multigol_q=1.25
                quota_combinata=doppia["q"]*multigol_q
                txt=f"{home} vs {away} | {doppia['e']} + Multigol 1-5 (Under 4.5) @ {quota_combinata:.2f}"
                cand.append({"q":quota_combinata,"txt":txt})
            except:
                continue
        if not cand:
            return "Nessuna BLASONATA oggi"
        cand=sorted(cand,key=lambda x:x["q"])[:10]
        body="\n".join([c["txt"] for c in cand])
        return f"BLASONATE OGGI - DOPPIA + MULTIGOL 1-5\nCome su Planetwin\n\n{body}"
    except Exception as e:
        return f"Errore: {e}"

def crea_schedina_oraria():
    global schedina_attiva, schedina_notificata
    try:
        fx=api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if not fx or fx=="LIMIT": return "
