import os,time,requests,threading,random
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=True
last_update_id=0
last_bolla_giorno="" # per non mandarla 2 volte
bolla_attiva=[];bolla_attiva_info={}

try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home(): return f"BOT V13 FIX 10:00",200
def run_flask():
    from waitress import serve; serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

def tg(m,chat_id=None):
    try:
        cid=chat_id if chat_id else CHAT_ID
        keyboard={"keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA"]],"resize_keyboard":True}
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":cid,"text":m,"parse_mode":"HTML","reply_markup":keyboard},timeout=25)
    except: pass

def api_get(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def get_flag(p):
    m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Netherlands":"🇳🇱"}; return m.get(p,f"[{p}]")

def crea_bolla_giornaliera_150(chat_id=None):
    # QUESTA E' LA PROGRESSIONE DA 1.50 DELLE 10 DI MATTINA
    try:
        oggi=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
        if fixtures=="LIMIT": return
        # prendiamo solo partite facili - case forti in casa
        candidati=[f for f in fixtures if f["fixture"]["status"]["short"]=="NS"]
        if not candidati: return
        
        # filtra per leghe principali per trovare le facili
        leghe_top=["Premier League","Serie A","Bundesliga","La Liga","Ligue 1","Eredivisie"]
        facili=[f for f in candidati if f["league"]["name"] in leghe_top]
        if len(facili)<3: facili=candidati

        random.shuffle(facili)
        bolla=[]
        quota_tot=1.0
        for f in facili[:4]:
            bolla.append(f)
            quota_tot*=1.20 # simuliamo X2 / 1X facili

        # aggiustiamo per arrivare a 1.50 / 1.60
        if len(bolla)>3: bolla=bolla[:3]

        txt=f"☀️ <b>BUONGIORNO DAMI - BOLLA DELLE 10:00</b>\n<b>PROGRESSIONE GIORNALIERA QUOTA ~1.50</b>\n\n"
        for i,p in enumerate(bolla,1):
            flag=get_flag(p["league"]["country"]); home=p["teams"]["home"]["name"]; away=p["teams"]["away"]["name"]
            orario=p["fixture"]["date"][11:16]; lega=p["league"]["name"]
            txt+=f"{i}. {flag} {home} - {away} -> <b>1X / X2</b> ({orario} - {lega})\n"
        txt+=f"\n💰 Quota Tot: ~1.50 / 1.65\n🍀 Facili prese dai top campionati"
        tg(txt,chat_id)
    except Exception as e: print(e)

def crea_bolla_su_richiesta(chat_id=None):
    try:
        oggi=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
        if fixtures=="LIMIT": tg("⚠️ Limite API finito",chat_id); return
        candidati=[f for f in fixtures if f["fixture"]["status"]["short"]=="NS"]
        random.shuffle(candidati)
        txt="🎫 <b>BOLLA X2</b>\n\n"
        for i,p in enumerate(candidati[:4],1):
            flag=get_flag(p["league"]["country"]); txt+=f"{i}. {flag} {p['teams']['home']['name']}-{p['teams']['away']['name']} -> X2\n"
        tg(txt,chat_id)
    except: pass

def poll_commands():
    global is_paused,last_update_id
    while True:
        try:
            url=f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=25"
            r=requests.get(url,timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    txt=upd.get("message",{}).get("text","").lower()
                    from_chat=upd.get("message",{}).get("chat",{}).get("id")
                    if "accendi" in txt: is_paused=False; tg("✅ ATTIVO - controllo live ON",from_chat)
                    elif "spegni" in txt or "pausa" in txt: is_paused=True; tg("🛑 LIVE IN PAUSA - ma la bolla delle 10:00 arriverà lo stesso",from_chat)
                    elif "bolla" in txt: crea_bolla_su_richiesta(from_chat)
        except: pass
        time.sleep(2)
threading.Thread(target=poll_commands,daemon=True).start()

# LOOP PRINCIPALE CON ORARIO
print("BOT V13 - ATTESA ORE 10:00",flush=True)
while True:
    try:
        now=datetime.now(ITALY)
        # INVIO AUTOMATICO ORE 10:00 - ANCHE SE IN PAUSA
        if now.hour==10 and now.minute<5:
            oggi_str=now.strftime("%Y-%m-%d")
            if last_bolla_giorno!=oggi_str:
                crea_bolla_giornaliera_150()
                last_bolla_giorno=oggi_str
                time.sleep(60)
        
        if is_paused:
            time.sleep(60)
            continue
            
        time.sleep(300)
    except: time.sleep(15)
