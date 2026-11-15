import os, time, threading, traceback
from datetime import datetime
import requests

BOT_TOKEN=os.getenv("BOT_TOKEN","")
CHAT_RAW=os.getenv("CHAT_ID","0") or "0"
CHAT_IDS=[int(x.strip()) for x in CHAT_RAW.replace(";",",").split(",") if x.strip().lstrip("-").isdigit()]
CHAT_ID=CHAT_IDS[0] if CHAT_IDS else 0
API_KEY=os.getenv("API_FOOTBALL_KEY","")
BASE_URL="https://v3.football.api-sports.io"
LEAGUE_LIVE_DELAY=50

TOP_NATIONS=["England","Spain","Germany","Italy","France","Portugal","Netherlands","Belgium","Turkey","Scotland","Austria","Switzerland","Denmark","Sweden","Norway","Poland","Czech Republic","Greece","Croatia","Serbia","Romania","Ukraine","Russia","Hungary","Bulgaria","Slovakia","Slovenia","Cyprus","Israel","Australia","USA","Brazil","Argentina"]

is_paused=False
sent_sfigata=set()
sent_preparati=set()
sent_bomba=set()

def tg(msg,cid=None,force=False):
    global is_paused
    if is_paused and not force:
        return
    try:
        targets=[cid] if cid else (CHAT_IDS if CHAT_IDS else [CHAT_ID])
        if not BOT_TOKEN: return
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for t in targets:
            try:
                requests.post(url,json={"chat_id":t,"text":msg,"parse_mode":"Markdown"},timeout=10)
                time.sleep(0.3)
            except: pass
    except: pass

def api(path,params=None):
    try:
        h={"x-apisports-key":API_KEY}
        r=requests.get(BASE_URL+path,headers=h,params=params or {},timeout=15)
        if r.status_code==200:
            return r.json().get("response",[])
        if r.status_code==429:
            time.sleep(60)
    except: pass
    return []

def get_live():
    return api("/fixtures", {"live":"all"})

# --- FUNZIONI PER I TASTI ---
def cmd_gialli():
    lives=get_live()
    trov=[]
    for f in lives[:50]:
        fid=f.get("fixture",{}).get("id")
        minute=f.get("fixture",{}).get("status",{}).get("elapsed") or 0
        if minute<20: continue
        st=api("/fixtures/statistics", {"fixture":fid})
        fouls=0
        for team in st:
            for s in team.get("statistics",[]):
                if "foul" in s.get("type","").lower():
                    v=s.get("value")
                    if v: fouls+=int(v)
        if fouls>=10:
            home=f.get("teams",{}).get("home",{}).get("name","")
            away=f.get("teams",{}).get("away",{}).get("name","")
            trov.append(f"🟨 {home}-{away} {minute}' Falli:{fouls}")
        time.sleep(0.5)
    if not trov:
        return "GIALLI 65%: Nessuna partita con tanti falli al momento. Riprova tra 10 min."
    return "🟨 GIALLI 65% LIVE:\n" + "\n".join(trov[:10])

def cmd_angoli():
    lives=get_live()
    trov=[]
    for f in lives[:50]:
        fid=f.get("fixture",{}).get("id")
        minute=f.get("fixture",{}).get("status",{}).get("elapsed") or 0
        if minute<10: continue
        st=api("/fixtures/statistics", {"fixture":fid})
        cor=0
        for team in st:
            for s in team.get("statistics",[]):
                if "corner" in s.get("type","").lower():
                    v=s.get("value")
                    if v: cor+=int(v)
        if cor>=6:
            home=f.get("teams",{}).get("home",{}).get("name","")
            away=f.get("teams",{}).get("away",{}).get("name","")
            trov.append(f"🚩 {home}-{away} {minute}' Angoli:{cor}")
        time.sleep(0.5)
    if not trov:
        return "ANGOLI +6: Nessuna partita con 6+ angoli ora."
    return "🚩 CALCIO D'ANGOLO +6:\n" + "\n".join(trov[:10])

def cmd_builder():
    lives=get_live()
    trov=[]
    for f in lives[:20]:
        home=f.get("teams",{}).get("home",{}).get("name","")
        away=f.get("teams",{}).get("away",{}).get("name","")
        minute=f.get("fixture",{}).get("status",{}).get("elapsed") or 0
        gh=f.get("goals",{}).get("home",0) or 0
        ga=f.get("goals",{}).get("away",0) or 0
        trov.append(f"🏗️ {home}-{away} {minute}' {gh}-{ga}")
    if not trov:
        return "BUILDER: Nessun live ora."
    return "🏗️ BAD BUILDER 1.82 WORLDWIDE (live ora):\n" + "\n".join(trov)

def live_loop():
    global is_paused
    print("AVVIO V57.3 FULL CON TASTI")
    tg("🤖 BOT V57.3 FULL ATTIVO\n✅ Tasti: GIALLI, ANGOLI, BUILDER, SFIGATA, PREPARATI, BOMBA\nTutto OK!",force=True)
    while True:
        try:
            if is_paused:
                time.sleep(5)
                continue
            lives=get_live()
            print(f"LIVE: {len(lives)} - {datetime.now()}")
            for f in lives:
                try:
                    fid=f.get("fixture",{}).get("id")
                    minute=f.get("fixture",{}).get("status",{}).get("elapsed")
                    if minute is None: continue
                    home=f.get("teams",{}).get("home",{}).get("name","")
                    away=f.get("teams",{}).get("away",{}).get("name","")
                    gh=f.get("goals",{}).get("home",0) or 0
                    ga=f.get("goals",{}).get("away",0) or 0
                    country=f.get("league",{}).get("country","")
                    league=f.get("league",{}).get("name","")
                    key=f"{home}-{away}"

                    if 30 <= minute <= 45 and key not in sent_preparati:
                        st=api("/fixtures/statistics", {"fixture":fid})
                        sot=0; cor=0
                        for team in st:
                            for s in team.get("statistics",[]):
                                t=s.get("type","").lower(); v=s.get("value")
                                if v is None: continue
                                if "on target" in t: sot+=int(v)
                                if "corner" in t: cor+=int(v)
                        if sot>=4 or cor>=6:
                            tg(f"⚠️ PREPARATI {minute}'\n{home} - {away}\n{gh}-{ga}\nTiri:{sot} Angoli:{cor}\n{league}")
                            sent_preparati.add(key)

                    if 60 <= minute <= 85 and key not in sent_bomba:
                        st=api("/fixtures/statistics", {"fixture":fid})
                        sot=0
                        for team in st:
                            for s in team.get("statistics",[]):
                                t=s.get("type","").lower(); v=s.get("value")
                                if v is None: continue
                                if "on target" in t: sot+=int(v)
                        if sot>=7:
                            tg(f"💣 BOMBA 7 TIRI {minute}'\n{home} - {away}\n{gh}-{ga} Tiri:{sot}\n{league}\nOVER 0.5")
                            sent_bomba.add(key)

                    if country in TOP_NATIONS and minute>=75 and key not in sent_sfigata:
                        if gh+ga<=1:
                            tg(f"🍀 SFIGATA {minute}'\n{home} - {away}\n{gh}-{ga}\n{league}")
                            sent_sfigata.add(key)
                    time.sleep(1.2)
                except: continue
            time.sleep(LEAGUE_LIVE_DELAY)
        except:
            traceback.print_exc()
            time.sleep(10)

def poll_loop():
    global is_paused
    last_id=0
    print("POLL ATTIVO V57.3")
    while True:
        try:
            if not BOT_TOKEN:
                time.sleep(10); continue
            url=f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            r=requests.get(url,params={"offset":last_id+1,"timeout":20},timeout=30).json()
            for upd in r.get("result",[]):
                last_id=upd["update_id"]
                msg=upd.get("message",{})
                txt=msg.get("text","") or ""
                cid=msg.get("chat",{}).get("id",0)
                low=txt.lower().strip()

                if "accendi" in low or "/start" in low:
                    is_paused=False
                    tg("BOT OK - TUTTO ATTIVO",cid,True)
                    continue
                if "spegni" in low or "pausa" in low:
                    is_paused=True
                    tg("BOT IN PAUSA",cid,True)
                    continue
                if low=="status":
                    tg(f"✅ BOT V57.3 FULL\nPausa:{is_paused}\nSfigata:{len(sent_sfigata)}\nPreparati:{len(sent_preparati)}\nBomba:{len(sent_bomba)}",cid,True)
                    continue
                if "reset" in low:
                    sent_sfigata.clear(); sent_preparati.clear(); sent_bomba.clear()
                    tg("RESET FATTO",cid,True)
                    continue
                if "gialli" in low:
                    tg("⏳ Cerco GIALLI...",cid,True)
                    res=cmd_gialli()
                    tg(res,cid,True)
                    continue
                if "angolo" in low:
                    tg("⏳ Cerco ANGOLI...",cid,True)
                    res=cmd_angoli()
                    tg(res,cid,True)
                    continue
                if "builder" in low or "bad builder" in low:
                    tg("⏳ Cerco BUILDER...",cid,True)
                    res=cmd_builder()
                    tg(res,cid,True)
                    continue
        except Exception as e:
            print("poll err",e)
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=live_loop,daemon=True).start()
    threading.Thread(target=poll_loop,daemon=True).start()
    while True:
        time.sleep(100)
