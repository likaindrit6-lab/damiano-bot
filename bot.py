import os, time, threading, traceback, requests
BOT_TOKEN=os.getenv("BOT_TOKEN","")
CHAT_RAW=os.getenv("CHAT_ID","0") or "0"
CHAT_IDS=[int(x.strip()) for x in CHAT_RAW.replace(";",",").split(",") if x.strip().lstrip("-").isdigit()]
CHAT_ID=CHAT_IDS[0] if CHAT_IDS else 0
API_KEY=os.getenv("API_FOOTBALL_KEY","")
BASE_URL="https://v3.football.api-sports.io"
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
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for t in targets:
            requests.post(url,json={"chat_id":t,"text":msg},timeout=10)
            time.sleep(0.2)
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
def do_search_gialli(cid):
    try:
        lives=get_live()
        if not lives:
            tg("GIALLI 65%: 0 live ora, riprova alle 15",cid,True)
            return
        trov=[]
        for f in lives[:20]:
            fid=f.get("fixture",{}).get("id")
            minute=f.get("fixture",{}).get("status",{}).get("elapsed") or 0
            home=f.get("teams",{}).get("home",{}).get("name","")
            away=f.get("teams",{}).get("away",{}).get("name","")
            st=api("/fixtures/statistics", {"fixture":fid})
            fouls=0
            for tm in st:
                for s in tm.get("statistics",[]):
                    if "foul" in s.get("type","").lower():
                        v=s.get("value")
                        if v: fouls+=int(v)
            if fouls>=10:
                trov.append(f"{home}-{away} {minute}' Falli {fouls}")
            time.sleep(0.3)
        if not trov:
            tg(f"GIALLI: controllati {len(lives)} live, nessuno con 10+ falli ora",cid,True)
        else:
            tg("GIALLI TROVATI:\n"+"\n".join(trov[:10]),cid,True)
    except Exception as e:
        tg(f"GIALLI errore {e}",cid,True)
def do_search_angoli(cid):
    try:
        lives=get_live()
        if not lives:
            tg("ANGOLI: 0 live ora",cid,True)
            return
        trov=[]
        for f in lives[:20]:
            fid=f.get("fixture",{}).get("id")
            minute=f.get("fixture",{}).get("status",{}).get("elapsed") or 0
            home=f.get("teams",{}).get("home",{}).get("name","")
            away=f.get("teams",{}).get("away",{}).get("name","")
            st=api("/fixtures/statistics", {"fixture":fid})
            cor=0
            for tm in st:
                for s in tm.get("statistics",[]):
                    if "corner" in s.get("type","").lower():
                        v=s.get("value")
                        if v: cor+=int(v)
            if cor>=6:
                trov.append(f"{home}-{away} {minute}' Angoli {cor}")
            time.sleep(0.3)
        if not trov:
            tg(f"ANGOLI: {len(lives)} live, nessuno con 6+ angoli",cid,True)
        else:
            tg("ANGOLI TROVATI:\n"+"\n".join(trov[:10]),cid,True)
    except Exception as e:
        tg(f"ANGOLI errore {e}",cid,True)
def live_loop():
    global is_paused
    print("AVVIO V57.6 FULL")
    tg("BOT V57.6 FULL ATTIVO - CON SFIGATA PREPARATI BOMBA + TASTI VERI",force=True)
    while True:
        try:
            if is_paused:
                time.sleep(5)
                continue
            lives=get_live()
            print(f"LIVE {len(lives)}")
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
                        for tm in st:
                            for s in tm.get("statistics",[]):
                                tp=s.get("type","").lower()
                                v=s.get("value")
                                if not v: continue
                                if "on target" in tp: sot+=int(v)
                                if "corner" in tp: cor+=int(v)
                        if sot>=4 or cor>=6:
                            tg(f"PREPARATI {minute}' {home}-{away} {gh}-{ga} Tiri {sot} Angoli {cor} {league}")
                            sent_preparati.add(key)
                    if 60 <= minute <= 85 and key not in sent_bomba:
                        st=api("/fixtures/statistics", {"fixture":fid})
                        sot=0
                        for tm in st:
                            for s in tm.get("statistics",[]):
                                if "on target" in s.get("type","").lower():
                                    v=s.get("value")
                                    if v: sot+=int(v)
                        if sot>=7:
                            tg(f"BOMBA 7 TIRI {minute}' {home}-{away} {gh}-{ga} Tiri {sot} {league}")
                            sent_bomba.add(key)
                    if country in TOP_NATIONS and minute>=75 and key not in sent_sfigata and gh+ga<=1:
                        tg(f"SFIGATA {minute}' {home}-{away} {gh}-{ga} {league}")
                        sent_sfigata.add(key)
                    time.sleep(1)
                except: continue
            time.sleep(50)
        except:
            traceback.print_exc()
            time.sleep(10)
def poll_loop():
    global is_paused
    last_id=0
    print("POLL V57.6")
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
                low=txt.lower()
                print(f"CMD {txt}")
                if "accendi" in low or "/start" in low:
                    is_paused=False
                    tg("BOT ACCESO",cid,True)
                    continue
                if "spegni" in low or "pausa" in low:
                    is_paused=True
                    tg("BOT IN PAUSA",cid,True)
                    continue
                if "status" in low:
                    lives=get_live()
                    tg(f"V57.6 FULL OK Live {len(lives)} Pausa {is_paused} Sfigata {len(sent_sfigata)}",cid,True)
                    continue
                if "reset" in low:
                    sent_sfigata.clear(); sent_preparati.clear(); sent_bomba.clear()
                    tg("RESET OK",cid,True)
                    continue
                if "gialli" in low:
                    tg("GIALLI 65% cerco partite vere 10 sec...",cid,True)
                    threading.Thread(target=do_search_gialli,args=(cid,),daemon=True).start()
                    continue
                if "angolo" in low:
                    tg("ANGOLO +6 cerco 10 sec...",cid,True)
                    threading.Thread(target=do_search_angoli,args=(cid,),daemon=True).start()
                    continue
                if "builder" in low or "doppia" in low or "bolla" in low or "over" in low:
                    lives=get_live()
                    tg(f"TASTO OK - Live ora {len(lives)} - Bot auto attivo",cid,True)
                    continue
        except Exception as e:
            print(f"poll err {e}")
            time.sleep(3)
if __name__=="__main__":
    threading.Thread(target=live_loop,daemon=True).start()
    threading.Thread(target=poll_loop,daemon=True).start()
    while True:
        time.sleep(100)
