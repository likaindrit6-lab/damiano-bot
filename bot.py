import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")

ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
live_inviate=set()
ultimo_gol={}
ultima_schedina_ora=-1
schedina_attiva=[]
schedina_notificata=set()

# pulizia webhook una volta sola
if BOT_TOKEN:
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
        print("Webhook pulito",flush=True)
    except: pass

app=Flask(__name__)
@app.route('/')
def home(): return "BOT V35 OK - NO CRASH",200
@app.route('/health')
def health(): return "OK",200

TASTIERA=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BLASONATE LUN-DOM","PARTITE OGGI"],["SCHEDINA ORA","TOKEN"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id or CHAT_ID
        if not BOT_TOKEN or not cid: return
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA
        # spezza messaggi lunghi
        if len(m)>3800:
            for i in range(0,len(m),3800):
                payload["text"]=m[i:i+3800]
                if i>0: payload.pop("reply_markup",None)
                requests.post(url,json=payload,timeout=15)
                time.sleep(0.3)
        else:
            requests.post(url,json=payload,timeout=15)
    except Exception as e:
        print("tg error",e,flush=True)

def api_get(url):
    if is_paused: return []
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=15)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def crea_schedina_oraria():
    global schedina_attiva, schedina_notificata
    try:
        fx=api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if fx=="LIMIT": return "Limite API - riprovo dopo"
        if not fx: return "Nessuna LIVE ora"
        cand=[]
        for p in fx:
            try:
                fid=p["fixture"]["id"]
                minute=p["fixture"]["status"]["elapsed"] or 0
                if minute<5 or minute>80: continue
                home=p['teams']['home']['name']; away=p['teams']['away']['name']
                # filtri base
                league=p['league']['name'].lower()
                if any(x in league for x in ["women","u19","u21","reserve","youth"]): continue
                if " ii" in (home+away).lower(): continue
                odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
                best=None
                for b in odds[0]["bookmakers"]:
                    for bet in b["bets"]:
                        if "double chance" in bet["name"].lower():
                            for v in bet["values"]:
                                if "home/away" in v["value"].lower(): continue
                                try:
                                    q=float(v["odd"])
                                    if 1.08 <= q <= 1.35:
                                        best={"q":q,"e":v["value"],"fid":fid,"home":home,"away":away,"lega":p['league']['name']}
                                except: pass
                if not best: continue
                txt=f"{minute}' {home} vs {away} | {best['e']} @ {best['q']} | {p['league']['name']}"
                cand.append({"q":best["q"],"txt":txt,"data":best})
            except: continue
        if len(cand)<2: return f"Poche LIVE sicure ora ({len(cand)})"
        cand=sorted(cand,key=lambda x:x["q"])
        picks=[]; tot=1.0
        for c in cand:
            if tot>=1.6: break
            picks.append(c); tot*=c["q"]
            if tot>1.9: tot/=c["q"]; picks.pop()
        if tot<1.55: return "Non riesco a fare 1.6 ora"
        schedina_attiva=[pk["data"] for pk in picks]
        schedina_notificata.clear()
        body="\n\n".join([p["txt"] for p in picks])
        return f"🔥 SCHEDINA ORARIA LIVE Quota {tot:.2f} - 90%\nTi avviso GOL e VINCENTE\n\n{body}\n\nTOT {tot:.2f}"
    except Exception as e:
        return f"Errore schedina: {e}"

def monitor_live():
    print("LIVE TRACKER ON",flush=True)
    while True:
        try:
            if is_paused: time.sleep(120); continue
            fx=api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if fx=="LIMIT" or not fx: time.sleep(90); continue
            for p in fx:
                try:
                    fid=p["fixture"]["id"]
                    minute=p["fixture"]["status"]["elapsed"]
                    if minute is None or minute>90: continue
                    if p["fixture"]["status"]["short"] not in ["1H","HT","2H"]: continue
                    home=p
