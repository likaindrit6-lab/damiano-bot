import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_id=0
av_g={}
av_s=set()
av_s_first=set()
TOP_LEAGUES={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,"Belarus":116,"Russia":235}
app=Flask(__name__)
@app.route("/")
def home():
    return "BOT V62 OK",200
TAST=json.dumps({"keyboard":[["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_CHIUSA=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False,chiusa=False):
    try:
        cid=cid or CHAT
        if not cid or not BOT:
            return
        base="https://api.telegram.org/bot"+BOT
        pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
        if keys:
            pay["reply_markup"]=json.loads(TAST_CHIUSA if chiusa else TAST)
        requests.post(base+"/sendMessage",json=pay,timeout=25)
    except:
        pass
def api(url):
    try:
        r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
        if r.status_code==429:
            return "LIMIT"
        return r.json().get("response",[])
    except:
        return []
def poll():
    global is_paused,last_id
    try:
        if BOT:
            requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true",timeout=10)
    except:
        pass
    while True:
        try:
            if not BOT:
                time.sleep(60)
                continue
            base="https://api.telegram.org/bot"+BOT
            r=requests.get(base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20",timeout=30).json()
            if r.get("ok"):
                for u in r.get("result",[]):
                    last_id=u["update_id"]
                    msg=u.get("message",{})
                    txt=(msg.get("text") or "").strip()
                    low=txt.lower()
                    cid=msg.get("chat",{}).get("id")
                    if not txt:
                        continue
                    if "chiudi menu" in low:
                        tg("Menu chiuso",cid,True,True)
                    elif "apri menu" in low:
                        tg("Menu aperto V62",cid,True,False)
                    elif "spegni" in low:
                        is_paused=True
                        tg("PAUSA",cid,True)
                    elif "accendi" in low or "/start" in low:
                        is_paused=False
                        tg("V62 ATTIVO - SOLO EUROPA",cid,True)
                    elif "status" in low:
                        tg("STATUS V62 OK",cid,True)
                    elif "bolla" in low:
                        tg("BOLLA OK - solo Europa",cid,True)
        except:
            pass
        time.sleep(2)
def live_loop():
    tg("BOT V62 ATTIVO - SOLO EUROPA",None,True)
    while True:
        try:
            if is_paused:
                time.sleep(30)
                continue
            now=datetime.now(ITALY)
            if 2<=now.hour<6:
                time.sleep(300)
                continue
            games=api("https://v3.football.api-sports.io/fixtures?live=all")
            if games=="LIMIT":
                time.sleep(3600)
                continue
            if not games:
                time.sleep(60)
                continue
            for g in games:
                lc=g.get("league",{}).get("country")
                lid=g.get("league",{}).get("id")
                if lc not in TOP_LEAGUES:
                    continue
                if TOP_LEAGUES.get(lc)!=lid:
                    continue
                fid=g.get("fixture",{}).get("id")
                mm=g.get("fixture",{}).get("status",{}).get("elapsed")
                if mm is None:
                    continue
                home=g.get("teams",{}).get("home",{}).get("name")
                away=g.get("teams",{}).get("away",{}).get("name")
                co=lc
                lg=g.get("league",{}).get("name") or ""
                gh=g.get("goals",{}).get("home")
                ga=g.get("goals",{}).get("away")
                if 30<=mm<=45 and fid not in av_s_first:
                    tg(f"PREPARATI {mm}' {co} - {lg} {home} {gh}-{ga} {away}")
                    av_s_first.add(fid)
                if 65<=mm<=90 and fid not in av_s:
                    tg(f"GIOCALO {mm}' {co} - {lg} {home} {gh}-{ga} {away}")
                    av_s.add(fid)
                    av_g[fid]=gh+ga
            for g in games:
                lc=g.get("league",{}).get("country")
                lid=g.get("league",{}).get("id")
                if lc not in TOP_LEAGUES:
                    continue
                if TOP_LEAGUES.get(lc)!=lid:
                    continue
                fid=g.get("fixture",{}).get("id")
                if fid in av_g:
                    gh2=g.get("goals",{}).get("home")
                    ga2=g.get("goals",{}).get("away")
                    if gh2+ga2>av_g[fid]:
                        hn=g.get("teams",{}).get("home",{}).get("name")
                        an=g.get("teams",{}).get("away",{}).get("name")
                        co2=g.get("league",{}).get("country")
                        lg2=g.get("league",{}).get("name")
                        tg(f"GOAL VINTO! {co2} - {lg2} {hn} {gh2}-{ga2} {an}")
                        del av_g[fid]
            time.sleep(60)
        except:
            time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=="__main__":
    PORT=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=PORT)
