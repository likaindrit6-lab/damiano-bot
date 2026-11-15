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
    if is_paused and not force: return
    try:
        targets=[cid] if cid else (CHAT_IDS if CHAT_IDS else [CHAT_ID])
        if not BOT_TOKEN: return
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for t in targets:
            try:
                requests.post(url,json={"chat_id":t,"text":msg,"parse_mode":"Markdown"},timeout=10)
                time.sleep(0.2)
            except: pass
    except: pass
def api(path,params=None):
    try:
        h={"x-apisports-key":API_KEY}
        r=requests.get(BASE_URL+path,headers=h,params=params or {},timeout=12)
        if r.status_code==200: return r.json().get("response",[])
    except: pass
    return []
def get_live():
    return api("/fixtures", {"live":"all"})
def background_search(cmd_type,cid):
    try:
        lives=get_live()
        if not lives:
            tg(f"{cmd_type}: 0 live ora! E' domenica mattina, le partite iniziano alle 15! Riprova dopo!",cid,True)
            return
        trov=[]
        for f in lives[:20]:
            fid=f.get("fixture",{}).get("id")
            minute=f.get("fixture",{}).get("status",{}).get("elapsed") or 0
            home=f.get("teams",{}).get("home",{}).get("name","")
            away=f.get("teams",{}).get("away",{}).get("name","")
            league=f.get("league",{}).get("name","")
            st=api("/fixtures/statistics", {"fixture":fid})
            cor=0; fouls=0; sot=0
            for team in st:
                for s in team.get("statistics",[]):
                    t=s.get("type","").lower(); v=s.get("value")
                    if v is None: continue
                    if "corner" in t: cor+=int(v)
                    if "foul" in t: fouls+=int(v)
                    if "on target" in t: sot+=int(v)
            if "GIALLO" in cmd_type and fouls>=8:
                trov.append(f"🟨 {home}-{away} {minute}' Falli:{fouls}")
            if "ANGOLO" in cmd_type and cor>=4:
                trov.append(f"🚩 {home}-{away} {minute}' Angoli:{cor}")
            if "BUILDER" in cmd_type:
                trov.append(f"🏗️ {home}-{away} {minute}' {league}")
            time.sleep(0.3)
        if not trov:
            tg(f"{cmd_type}: Ho guardato {len(lives)} live, 0 partite con requisiti. Live totali: {len(lives)}",cid,True)
        else:
            tg(f"{cmd_type} TROVATE:\n" + "\n".join(trov[:10]),cid,True)
    except Exception as e:
        tg(f"{cmd_type}: Errore {e}",cid,True)
def live_loop():
    global is_paused
    print("AVVIO V57.5 VERA")
    tg("🤖 BOT V57.5 VERA ATTIVO\nLive auto + t
