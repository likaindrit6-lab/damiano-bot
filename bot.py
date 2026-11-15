import os, time, threading, traceback, requests
from datetime import datetime
BOT_TOKEN=os.getenv("BOT_TOKEN","")
CHAT_RAW=os.getenv("CHAT_ID","0") or "0"
CHAT_IDS=[int(x.strip()) for x in CHAT_RAW.replace(";",",").split(",") if x.strip().lstrip("-").isdigit()]
CHAT_ID=CHAT_IDS[0] if CHAT_IDS else 0
API_KEY=os.getenv("API_FOOTBALL_KEY","")
BASE_URL="https://v3.football.api-sports.io"
TOP_NATIONS=["England","Spain","Germany","Italy","France","Portugal","Netherlands","Belgium","Turkey","Scotland","Austria","Switzerland","Denmark","Sweden","Norway","Poland","Czech Republic","Greece","Croatia","Serbia","Romania","Ukraine","Russia","Hungary","Bulgaria","Slovakia","Slovenia","Cyprus","Israel","Australia","USA","Brazil","Argentina"]
is_paused=False
sent_sfigata_goal=set()
sent_sfigata_ht=set()
sent_preparati=set()
sent_bomba=set()
last_scores={}
def tg(msg,cid=None,force=False):
    global is_paused
    if is_paused and not force: return
    try:
        targets=[cid] if cid else (CHAT_IDS if CHAT_IDS else [CHAT_ID])
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for t in targets:
            requests.post(url,json={"chat_id":t,"text":msg},timeout=12)
            time.sleep(0.2)
    except: pass
def api(path,params=None):
    try:
        h={"x-apisports-key":API_KEY}
        r=requests.get(BASE_URL+path,headers=h,params=params or {},timeout=15)
        if r.status_code==200: return r.json().get("response",[])
    except: pass
    return []
def get_live(): return api("/fixtures", {"live":"all"})
def get_today():
    today=datetime.now().strftime("%Y-%m-%d")
    return api("/fixtures", {"date":today})
def get_odds(fid):
    try:
        for o in api("/odds", {"fixture":fid}):
            for b in o.get("bookmakers",[]):
                for bet in b.get("bets",[]):
                    if bet.get("name")=="Match Winner":
                        v=bet.get("values",[])
                        if len(v)>=3:
                            return float(v[0].get("odd",0)), float(v[2].get("odd",0))
    except: pass
    return 0,0
def avg_cards_team(team_id):
    try:
        last=api("/fixtures", {"team":team_id,"last":5})
        tot=0
        for f in last:
            fid=f.get("fixture",{}).get("id")
            st=api("/fixtures/statistics", {"fixture":fid})
            for tm in st:
                for s in tm.get("statistics",[]):
                    if "yellow" in s.get("type","").lower():
                        v=s.get("value")
                        if v: tot+=int(v)
        return tot/5 if last else 0
    except: return 0
def do_search_gialli(cid):
    try:
        tg("🟨 GIALLI 65% PRE-MATCH: cerco oggi...",cid,True)
        tod=get_today()
        trov=[]
        for f in tod[:40]:
            if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
            country=f.get("league",{}).get("country","")
            if country not in TOP_NATIONS: continue
            hid=f.get("teams",{}).get("home",{}).get("id")
            aid=f.get("teams",{}).get("away",{}).get("id")
            home=f.get("teams",{}).get("home",{}).get("name","")
            away=f.get("teams",{}).get("away",{}).get("name","")
            league=f.get("league",{}).get("name","")
            avg_h=avg_cards_team(hid)
            avg_a=avg_cards_team(aid)
            avg_tot=avg_h+avg_a
            if avg_tot>=3.0:
                hour=f.get("fixture",{}).get("date","")[11:16]
                trov.append(f"{hour} {home}-{away} {country} {league} gialli {avg_tot:.1f}")
            time.sleep(0.4)
        tg("🟨 GIALLI 65% OGGI:\n"+"\n".join(trov[:15]) if trov else "🟨 GIALLI: nessuna oggi",cid,True)
    except Exception as e: tg(f"GIALLI err {e}",cid,True)
def do_search_angoli(cid):
    try:
        tg("🚩 ANGOLI +6 PRE-MATCH...",cid,True)
        tod=get_today()
        trov=[]
        for f in tod[:35]:
            if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
            home=f.get("teams",{}).get("home",{}).get("name","")
            away=f.get("teams",{}).get("away",{}).get("name","")
            league=f.get("league",{}).get("name","")
            country=f.get("league",{}).get("country","")
            hour=f.get("fixture",{}).get("date","")[11:16]
            trov.append(f"{hour} {home}-{away} {country} {league}")
        tg("🚩 ANGOLI +6 OGGI:\n"+"\n".join(trov[:12]) if trov else "🚩 ANGOLI: 0",cid,True)
    except Exception as e: tg(f"ANGOLI err {e}",cid,True)
def live_loop():
    global last_scores
    print("AVVIO V59.2 NAZIONE")
    tg("🤖 BOT V59.2 ATTIVA\n⚫ SFIGATA 4.50+ CON NAZIONE",force=True)
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
                    if minute is None: minute=0
                    home=f.get("teams",{}).get("home",{}).get("name","")
                    away=f.get("teams",{}).get("away",{}).get("name","")
                    gh=f.get("goals",{}).get("home",0) or 0
                    ga=f.get("goals",{}).get("away",0) or 0
                    league=f.get("league",{}).get("name","")
                    country=f.get("league",{}).get("country","")
                    stats=api("/fixtures/statistics", {"fixture":fid})
                    sot=0; cor=0
                    for tm in stats:
                        for s in tm.get("statistics",[]):
                            tp=str(s.get("type","")).lower()
                            v=s.get("value")
                            if v is None: continue
                            try:
                                if "on target" in tp: sot+=int(v)
                                if "corner" in tp: cor+=int(v)
                            except: pass
                    if 30 <= minute <= 45 and fid not in sent_preparati:
                        if sot>=4 or cor>=6:
                            tg(f"🔥 PREPARATI {minute}' {home}-{away} {gh}-{ga} Tiri {sot} Angoli {cor}\n{country} - {league}")
                            sent_preparati.add(fid)
                    if 60 <= minute <= 85 and fid not in sent_bomba:
                        if sot>=7:
                            tg(f"🚀 BOMBA 7 TIRI {minute}' {home}-{away} {gh}-{ga} Tiri {sot}\n{country} - {league}")
                            sent_bomba.add(fid)
                    ho,ao=get_odds(fid)
                    if ho>=4.5 or ao>=4.5:
                        sfig_team=home if ho>=4.5 and ho>ao else away if ao>=4.5 and ao>ho else None
                        quota=ho if sfig_team==home else ao if sfig_team==away else 0
                        is_home=sfig_team==home
                        if sfig_team:
                            prev=last_scores.get(fid,(0,0))
                            scored=(is_home and gh>prev[0]) or (not is_home and ga>prev[1])
                            if scored and fid not in sent_sfigata_goal:
                                tg(f"⚫ SFIGATA GOAL! {minute}'\n{sfig_team} QUOTA {quota}\n{home}-{away} {gh}-{ga}\n{country} - {league}")
                                sent_sfigata_goal.add(fid)
                            if 44 <= minute <= 52 and gh==ga and fid not in sent_sfigata_ht:
                                tg(f"⚫ SFIGATA HT PARI! {minute}'\n{sfig_team} QUOTA {quota} STA PAREGGIANDO\n{home}-{away} {gh}-{ga}\n{country} - {league}")
                                sent_sfigata_ht.add(fid)
                    last_scores[fid]=(gh,ga)
                    time.sleep(0.5)
                except: continue
            time.sleep(35)
        except:
            traceback.print_exc()
            time.sleep(10)
def poll_loop():
    global is_paused
    last_id=0
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
                if "accendi" in low or "/start" in low:
                    is_paused=False
                    tg("✅ BOT ACCESO V59.2",cid,True)
                    continue
                if "spegni" in low or "pausa" in low:
                    is_paused=True
                    tg("⏸️ BOT IN PAUSA",cid,True)
                    continue
                if "status" in low:
                    lives=get_live()
                    tg(f"📊 V59.2 STATUS\nLive {len(lives)}\n🔥 {len(sent_preparati)} 🚀 {len(sent_bomba)}\n⚫ Goal {len(sent_sfigata_goal)} HT {len(sent_sfigata_ht)}",cid,True)
                    continue
                if "reset" in low:
                    sent_preparati.clear(); sent_bomba.clear(); sent_sfigata_goal.clear(); sent_sfigata_ht.clear(); last_scores.clear()
                    tg("🔄 RESET OK",cid,True)
                    continue
                if "gialli" in low:
                    threading.Thread(target=do_search_gialli,args=(cid,),daemon=True).start()
                    continue
                if "angoli" in low or "angolo" in low:
                    threading.Thread(target=do_search_angoli,args=(cid,),daemon=True).start()
                    continue
                if "builder" in low or "doppia" in low or "bolla" in low or "over" in low:
                    tg(f"🟢 TASTO {txt} OK",cid,True)
                    continue
        except Exception as e:
            print(f"poll err {e}")
            time.sleep(3)
if __name__=="__main__":
    threading.Thread(target=live_loop,daemon=True).start()
    threading.Thread(target=poll_loop,daemon=True).start()
    while True: time.sleep(100)
