import os, time, threading, traceback, json, re
from datetime import datetime, timedelta
import requests

BOT_TOKEN=os.getenv("BOT_TOKEN","")
CHAT_ID=int(os.getenv("CHAT_ID","0") or 0)
API_KEY=os.getenv("API_FOOTBALL_KEY","")
BASE_URL="https://v3.football.api-sports.io"
LEAGUE_LIVE_DELAY=50
POLL_INTERVAL=8

TOP_NATIONS=["England","Spain","Germany","Italy","France","Portugal","Netherlands","Belgium","Turkey","Scotland","Austria","Switzerland","Denmark","Sweden","Norway","Poland","Czech Republic","Greece","Croatia","Serbia","Romania","Ukraine","Russia","Hungary","Bulgaria","Slovakia","Slovenia","Cyprus","Israel","Australia","USA","Brazil","Argentina"]

is_paused=False
sent_sfigata=set()
sent_preparati=set()
sent_bomba=set()
sent_gol=set()
sent_15=set()
sent_gialli=set()
sent_angoli=set()

def tg(msg,cid=None,force=False):
    global is_paused
    if is_paused and not force:
        return
    try:
        target=cid or CHAT_ID
        if not BOT_TOKEN or not target:
            return
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url,json={"chat_id":target,"text":msg,"parse_mode":"Markdown"},timeout=10)
    except:
        pass

def api(path,params=None):
    try:
        h={"x-apisports-key":API_KEY}
        r=requests.get(BASE_URL+path,headers=h,params=params or {},timeout=15)
        if r.status_code==200:
            return r.json().get("response",[])
        if r.status_code==429:
            print("LIMIT API")
            time.sleep(60)
    except Exception as e:
        print("api err",e)
    return []

def get_live():
    return api("/fixtures", {"live":"all"})

def get_stats(fid):
    return api("/fixtures/statistics", {"fixture":fid})

def parse_sot(stats):
    try:
        for team in stats:
            for s in team.get("statistics",[]):
                if "on target" in s.get("type","").lower() or "shots on goal" in s.get("type","").lower():
                    v=s.get("value")
                    if v is not None:
                        return int(v)
    except:
        pass
    return 0

def parse_corners(stats):
    try:
        for team in stats:
            for s in team.get("statistics",[]):
                if "corner" in s.get("type","").lower():
                    v=s.get("value")
                    if v is not None:
                        return int(v)
    except:
        pass
    return 0

def live_loop():
    global is_paused
    print("AVVIO V57.1 FINALE FIXED - SFIGATA + PREPARATI + BOMBA 7 TIRI")
    tg("🤖 BOT V57.1 ATTIVO\nSFIGATA + PREPARATI 30-45 + BOMBA 7 TIRI 60-85\nScrivi STATUS per controllo",force=True)
    while True:
        try:
            if is_paused:
                time.sleep(5)
                continue
            lives=get_live()
            print(f"LIVE trovate: {len(lives)} - {datetime.now()}")
            for f in lives:
                try:
                    fid=f.get("fixture",{}).get("id")
                    minute=f.get("fixture",{}).get("status",{}).get("elapsed")
                    if minute is None:
                        continue
                    home=f.get("teams",{}).get("home",{}).get("name","")
                    away=f.get("teams",{}).get("away",{}).get("name","")
                    gh=f.get("goals",{}).get("home",0) or 0
                    ga=f.get("goals",{}).get("away",0) or 0
                    country=f.get("league",{}).get("country","")
                    league=f.get("league",{}).get("name","")
                    key=f"{home}-{away}"

                    # --- PREPARATI 30-45 con 4 tiri ---
                    if 30 <= minute <= 45 and key not in sent_preparati:
                        st=api("/fixtures/statistics", {"fixture":fid})
                        sot=0
                        cor=0
                        for team in st:
                            for s in team.get("statistics",[]):
                                t=s.get("type","").lower()
                                v=s.get("value")
                                if v is None:
                                    continue
                                if "on target" in t:
                                    sot+=int(v)
                                if "corner" in t:
                                    cor+=int(v)
                        if sot>=4 or cor>=6:
                            msg=f"⚠️ PREPARATI {minute}'\n{home} - {away}\n{gh}-{ga}\nTiri: {sot} | Angoli: {cor}\n{league}"
                            tg(msg)
                            sent_preparati.add(key)

                    # --- BOMBA 7 TIRI 60-85 qualsiasi risultato ---
                    if 60 <= minute <= 85 and key not in sent_bomba:
                        st=api("/fixtures/statistics", {"fixture":fid})
                        sot=0
                        for team in st:
                            for s in team.get("statistics",[]):
                                t=s.get("type","").lower()
                                v=s.get("value")
                                if v is None:
                                    continue
                                if "on target" in t:
                                    sot+=int(v)
                        if sot>=7:
                            msg=f"💣 BOMBA 7 TIRI {minute}'\n{home} - {away}\nRISULTATO: {gh}-{ga}\nTiri in porta: {sot}\nLEGA: {league}\n➡️ OVER 0.5 / GOL"
                            tg(msg)
                            sent_bomba.add(key)

                    # --- SFIGATA per TOP ---
                    if country in TOP_NATIONS and minute>=75 and (gh==0 or ga==0) and key not in sent_sfigata:
                        if gh+ga<=1:
                            msg=f"🍀 SFIGATA {minute}'\n{home} - {away}\n{gh}-{ga}\n{league} ({country})"
                            tg(msg)
                            sent_sfigata.add(key)

                    time.sleep(1.2)
                except Exception as e:
                    print("inner",e)
                    continue
            time.sleep(LEAGUE_LIVE_DELAY)
        except Exception as e:
            print("loop err",e)
            traceback.print_exc()
            time.sleep(10)

def poll_loop():
    global is_paused
    last_id=0
    print("POLL ATTIVO")
    while True:
        try:
            if not BOT_TOKEN:
                time.sleep(10)
                continue
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
                    tg("BOT OK",cid,True)
                    continue

                if "spegni" in low or "pausa" in low:
                    is_paused=True
                    tg("BOT IN PAUSA",cid,True)
                    continue

                if "status" in low:
                    inf=f"✅ BOT V57.1 ATTIVO\nPausa: {is_paused}\nInviati:\nSfigata:{len(sent_sfigata)}\nPreparati:{len(sent_preparati)}\nBomba:{len(sent_bomba)}"
                    tg(inf,cid,True)
                    continue

                if "reset" in low:
                    sent_sfigata.clear()
                    sent_preparati.clear()
                    sent_bomba.clear()
                    tg("RESET FATTO",cid,True)
                    continue
        except Exception as e:
            print("poll err",e)
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=live_loop,daemon=True).start()
    threading.Thread(target=poll_loop,daemon=True).start()
    while True:
        time.sleep(100)
