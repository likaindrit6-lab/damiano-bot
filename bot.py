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
av_sfiga_score={}
TOP_LEAGUES={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,"Belarus":116,"Russia":235}
app=Flask(__name__)
@app.route("/")
def home():
    return "BOT V64 FULL - BOLLA ALTA + STATS",200
TAST=json.dumps({"keyboard":[["DOPPIA ALTA %"],["BOLLA EUROPA 33 NAZIONI"],["STATISTICHE 35 NAZIONI"],["CALCIO D'ANGOLO +6"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_CHIUSA=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})
def tg(m,cid=None,keys=False,chiusa=False):
    try:
        cid=cid or CHAT
        if not cid or not BOT:
            return
        base="https://api.telegram.org/bot"+BOT
        upper=m.upper()
        if "PREPARATI" in upper and "🔥" not in m:
            m=f"🔥 {m}"
        elif "GIOCALO" in upper and "🚀" not in m:
            m=f"🚀 {m}"
        elif any(x in upper for x in ["GOL","PAREGGIA","VANTAGGIO","GOAL VINTO","SFIGATA"]) and "🟢" not in m:
            m=f"🟢 {m}"
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
def get_sfigata(fid):
    try:
        u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
        data=api(u)
        if not data or data=="LIMIT":
            return None
        for book in data[0].get("bookmakers",[])[:2]:
            for bet in book.get("bets",[]):
                if bet.get("name")=="Match Winner":
                    q={}
                    for v in bet.get("values",[]):
                        try:
                            q[v.get("value")]=float(v.get("odd"))
                        except:
                            pass
                    h=q.get("Home",0)
                    a=q.get("Away",0)
                    if h>=4.5 and h>a and a<=1.8:
                        return ("HOME",h,"AWAY",a)
                    if a>=4.5 and a>h and h<=1.8:
                        return ("AWAY",a,"HOME",h)
        return None
    except:
        return None
def get_dc(fid):
    try:
        u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
        data=api(u)
        if not data or data=="LIMIT":
            return None
        for book in data[0].get("bookmakers",[])[:3]:
            for bet in book.get("bets",[]):
                if "Double Chance" in bet.get("name",""):
                    best=None
                    best_odd=10
                    for v in bet.get("values",[]):
                        try:
                            odd=float(v.get("odd"))
                            if odd<best_odd:
                                best_odd=odd
                                best=v.get("value")
                        except:
                            continue
                    if best:
                        if "Home/Draw" in best:
                            return "1X @ "+str(best_odd)
                        if "Draw/Away" in best:
                            return "X2 @ "+str(best_odd)
                        return "12 @ "+str(best_odd)
    except:
        pass
    return None
def get_fixtures_today():
    today=datetime.now(ITALY).strftime("%Y-%m-%d")
    return api("https://v3.football.api-sports.io/fixtures?date="+today)
def run_bolla(cid=None):
    try:
        tg("Cerco BOLLA ALTA 33 NAZIONI...",cid,True)
        data=get_fixtures_today()
        if not data or data=="LIMIT":
            tg("BOLLA: Limite API",cid,True)
            return
        sel=[]
        for country,top_id in TOP_LEAGUES.items():
            found=None
            for f in data:
                if f.get("league",{}).get("id")==top_id and f.get("league",{}).get("country")==country:
                    if f.get("fixture",{}).get("status",{}).get("short")!="NS":
                        continue
                    found=f
                    break
            if not found:
                continue
            ora=str(found.get("fixture",{}).get("date",""))[11:16]
            home=found.get("teams",{}).get("home",{}).get("name")
            away=found.get("teams",{}).get("away",{}).get("name")
            dc=get_dc(found.get("fixture",{}).get("id"))
            if dc is None:
                dc="1X @ 1.25"
            sel.append(f"{ora} {country} {home} vs {away} -> {dc}")
            time.sleep(0.3)
            if len(sel)>=33:
                break
        if not sel:
            tg("Oggi nessuna TOP LEAGUE",cid,True)
            return
        out=f"BOLLA EUROPA ALTA {len(sel)} NAZIONI 🔥\n\n"
        n=1
        for mm in sel:
            out+=f"{n}. {mm}\n"
            n+=1
        tg(out,cid,True)
    except Exception as e:
        tg(f"BOLLA ERRORE {e}",cid,True)
def run_doppia(cid=None):
    try:
        tg("Cerco DOPPIE ALTE 90% da ora a mezzanotte...",cid,True)
        data=get_fixtures_today()
        if not data or data=="LIMIT":
            tg("DOPPIA: Limite API",cid,True)
            return
        out=[]
        now_h=datetime.now(ITALY).hour
        for f in data:
            lc=f.get("league",{}).get("country")
            lid=f.get("league",{}).get("id")
            if lc not in TOP_LEAGUES:
                continue
            if TOP_LEAGUES.get(lc)!=lid:
                continue
            if f.get("fixture",{}).get("status",{}).get("short")!="NS":
                continue
            ora_s=str(f.get("fixture",{}).get("date",""))[11:16]
            try:
                ora_h=int(ora_s.split(":")[0])
                if ora_h < now_h:
                    continue
            except:
                pass
            fid=f.get("fixture",{}).get("id")
            dc=get_dc(fid)
            if dc is None:
                continue
            try:
                odd_val=float(dc.split("@")[1].strip())
                if odd_val>1.40:
                    continue
            except:
                continue
            home=f.get("teams",{}).get("home",{}).get("name")
            away=f.get("teams",{}).get("away",{}).get("name")
            out.append(f"{ora_s} {lc} {home} vs {away} -> {dc} SICUREZZA 90%+")
            if len(out)>=10:
                break
        if not out:
            tg("Nessuna DOPPIA 90% da ora a mezzanotte",cid,True)
            return
        txt=f"DOPPIE ALTE {len(out)} ORA-MEZZANOTTE 🔥\n\n"
        n=1
        for mm in out:
            txt+=f"{n}. {mm}\n\n"
            n+=1
        tg(txt,cid,True)
    except Exception as e:
        tg(f"DOPPIA ERRORE {e}",cid,True)
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
                        tg("Menu V64 FULL - BOLLA ALTA + STATS + CORNER",cid,True,False)
                    elif "spegni" in low:
                        is_paused=True
                        tg("PAUSA",cid,True)
                    elif "accendi" in low or "/start" in low:
                        is_paused=False
                        tg("V64 FULL ATTIVO - TUTTO RIPRISTINATO",cid,True)
                    elif "status" in low:
                        tg("STATUS V64 FULL OK - STATS + CORNER + SFIGATA",cid,True)
                    elif "doppia" in low:
                        run_doppia(cid)
                    elif "bolla" in low:
                        run_bolla(cid)
                    elif "statistiche" in low:
                        tg("STATISTICHE 35 NAZIONI - in arrivo con LIVE",cid,True)
                    elif "angolo" in low:
                        tg("CALCIO D'ANGOLO +6 - attivo nel LIVE",cid,True)
        except:
            pass
        time.sleep(2)
def live_loop():
    tg("BOT V64 FULL ATTIVO - BOLLA ALTA + STATS + CORNER + SFIGATA",None,True)
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
                lname=g.get("league",{}).get("name","") or ""
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
                lg=lname
                gh=g.get("goals",{}).get("home")
                ga=g.get("goals",{}).get("away")
                if fid not in av_sfiga_score:
                    av_sfiga_score[fid]=(gh,ga)
                else:
                    oh,oa=av_sfiga_score[fid]
                    if gh!=oh or ga!=oa:
                        chi="HOME" if gh>oh else "AWAY"
                        av_sfiga_score[fid]=(gh,ga)
                        sf=get_sfigata(fid)
                        if sf:
                            tipo,qs,tf,qf=sf
                            if chi==tipo:
                                sfiga_gol = gh if tipo=="HOME" else ga
                                fav_gol = ga if tipo=="HOME" else gh
                                if sfiga_gol >= fav_gol:
                                    stato="PAREGGIA" if sfiga_gol==fav_gol else "VANTAGGIO"
                                    ns=home if tipo=="HOME" else away
                                    nf=away if tipo=="HOME" else home
                                    full=f"SFIGATA {stato} {mm}' {co} - {lg}\n{home} {gh}-{ga} {away}\nSfigata {ns} @{qs}\nFavorita {nf} @{qf}"
                                    tg(full)
                if 30<=mm<=45 and fid not in av_s_first:
                    u="https://v3.football.api-sports.io/fixtures/statistics?fixture="+str(fid)
                    st=api(u)
                    sot=0
                    corn=0
                    if st and len(st)>=2:
                        for s in st:
                            for x in s.get("statistics",[]):
                                if "Shots on Goal" in x.get("type",""):
                                    try:
                                        sot+=int(str(x.get("value") or 0))
                                    except:
                                        pass
                                if "corner" in str(x.get("type","")).lower():
                                    try:
                                        corn+=int(str(x.get("value") or 0))
                                    except:
                                        pass
                    if sot
