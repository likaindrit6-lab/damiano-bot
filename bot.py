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

# --- FUNZIONI TUE IDENTICHE ---
TASTIERA_JSON=json.dumps({
    "keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"]],
    "resize_keyboard":True,"is_persistent":True
})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        if not BOT_TOKEN or not cid: return
        base=f"https://api.telegram.org/bot{BOT_TOKEN}"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA_JSON
        requests.post(base+"/sendMessage",json=payload,timeout=25)
    except: pass

def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def crea_bolla_15():
    try:
        picks=[]; quota_tot=1.0
        BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly","Amateur","Club Friend"]
        for gg in range(3):
            if len(picks)>=20: break
            giorno=(datetime.now(ITALY)+timedelta(days=gg)).strftime("%Y-%m-%d")
            fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
            if not fixtures: continue
            fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
            for p in fixtures:
                if len(picks)>=20: break
                if any(b.lower() in p["league"]["name"].lower() for b in BAN): continue
                fid=p["fixture"]["id"]
                dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
                if dt < datetime.now(ITALY): continue
                home=p['teams']['home']['name']; away=p['teams']['away']['name']
                paese=p['league']['country']; lega=p['league']['name']
                orario=dt.strftime("%H:%M")
                qenc=urllib.parse.quote_plus(home+" "+away)
                qenc_bet=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
                link_bet365=f"https://www.google.com/search?q={qenc_bet}&btnI=1"
                link_stats=f"https://www.flashscore.it/search/?q={qenc}"
                odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                if not odds or odds=="LIMIT": continue
                if not odds[0].get("bookmakers"): continue
                try:
                    over=None
                    for bet in odds[0]["bookmakers"][0]["bets"]:
                        if "Over/Under" not in bet["name"]: continue
                        for v in bet["values"]:
                            if "Over 0.5" in v["value"]:
                                try:
                                    q=float(v["odd"])
                                    if 1.01 <= q <= 1.35:
                                        over=q; break
                                except: continue
                        if over: break
                    if not over: continue
                    quota_tot=round(quota_tot*over,2)
                    picks.append(f"🕐 {orario} {giorno[5:10]} - {paese} - {lega}\n{home} vs {away}\n👉 Over 0.5 @ {over}\n<a href='{link_bet365}'>BET365</a> | <a href='{link_stats}'>STATS</a>")
                except: continue
        if len(picks)<5: return f"Oggi poche partite, trovate {len(picks)}"
        return f"🔥 BOLLA OVER 0.5 - {len(picks)} PARTITE - Quota {quota_tot:.2f} 🔥\n\n"+"\n\n".join(picks)+f"\n\n💰 TOT {quota_tot:.2f}"
    except Exception as e: return f"Errore bolla: {e}"

def poll_commands():
    global is_paused,last_update_id
    try:
        if BOT_TOKEN:
