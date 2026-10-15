import os, time, requests, threading, json
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")
KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))
last_id = 0

TOP33 = {
"Italia":135,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,
"Portogallo":94,"Olanda":88,"Belgio":144,"Turchia":203,"Scozia":179,
"Austria":218,"Svizzera":207,"Danimarca":119,"Svezia":113,"Norvegia":103,
"Polonia":106,"Rep Ceca":110,"Croazia":210,"Serbia":286,"Grecia":197,
"Romania":283,"Ungheria":271,"Bulgaria":172,"Slovacchia":334,"Slovenia":373,
"Cipro":318,"Israele":383,"Ucraina":333,"Bielorussia":116,"Irlanda":84,
"Irlanda Nord":410,"Galles":1107,"Islanda":108
}

LEAGUES = {"Serie A":135,"Serie B":136,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,"Olanda":88,"Portogallo":94,"Turchia":203,"Belgio":144}

app = Flask(__name__)
@app.route("/")
def home(): return "V63 COMPLETO TUTTA ROBA TUA + 33 OK", 200

TAST = json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["LIVE","RIPARTITE"],["PRIMO TEMPO","PREPARATI E SEGNA"],["DOPPIA 90%","BOLLA EUROPA 33 NAZIONI"],["STATUS"]],"resize_keyboard":True})

def tg(m, cid=None, keys=False):
    try:
        cid = cid or CHAT
        b = "https://api.telegram.org/bot" + BOT
        pay = {"chat_id": cid, "text": m, "parse_mode": "HTML"}
        if keys: pay["reply_markup"] = json.loads(TAST)
        requests.post(b + "/sendMessage", json=pay, timeout=25)
    except: pass

def api(u):
    try:
        r = requests.get(u, headers={"x-apisports-key": KEY}, timeout=30)
        return r.json().get("response", [])
    except: return []

def get_stats(team_id):
    last = api("https://v3.football.api-sports.io/fixtures?team=" + str(team_id) + "&last=10&season=2024")
    gf=0;gs=0;tot=0;win=0;uh=0;ua=0;btts=0;c=0
    for p in last:
        gh = p["goals"]["home"]; ga = p["goals"]["away"]
        if gh is None: continue
        hid = p["teams"]["home"]["id"]
        is_home = hid == team_id
        if is_home:
            gf+=gh; gs+=ga
            if gh>=ga: uh+=1
            if gh>ga: win+=1
        else:
            gf+=ga; gs+=gh
            if ga>=gh: ua+=1
            if ga>gh: win+=1
        if gh>0 and ga>0: btts+=1
        tot+=gh+ga; c+=1
    if c==0: return None
    return {"gf":gf,"gs":gs,"avg":tot/c,"win":win/c,"uh":uh,"ua":ua,"btts":btts/c}

# --- ROBA TUA VECCHIA ---

def run_live(cid=None):
    data = api("https://v3.football.api-sports.io/fixtures?live=all")
    msg = "LIVE ORA - 1X SICURI\n\n"
    for fx in data[:15]:
        home=fx["teams"]["home"]["name"]; away=fx["teams"]["away"]["name"]
        gh=fx["goals"]["home"]; ga=fx["goals"]["away"]
        minuto=str(fx["fixture"]["status"]["elapsed"])+"'"
        if gh==ga: msg+= minuto + " " + home + " " + str(gh) + "-" + str(ga) + " " + away + " -> 1X LIVE\n"
    tg(msg, cid, True)

def run_ripartite(cid=None):
    data = api("https://v3.football.api-sports.io/fixtures?live=all")
    msg = "RIPARTITE - SECONDO TEMPO APPENA INIZIATO\n\n"
    for fx in data:
        st=fx["fixture"]["status"]["short"]
        el=fx["fixture"]["status"]["elapsed"]
        if el and 45 <= el <= 55:
            home=fx["teams"]["home"]["name"]; away=fx["teams"]["away"]["name"]
            gh=fx["goals"]["home"]; ga=fx["goals"]["away"]
            msg+= str(el) + "' " + home + " " + str(gh) + "-" + str(ga) + " " + away + " -> RIPARTITA\n"
    tg(msg, cid, True)

def run_primo_tempo(cid=None):
    msg = "PRIMO TEMPO - OVER 0.5 PT\n\n"
    for d in range(0,1):
        date = (datetime.now(ITALY) + timedelta(days=d)).strftime("%Y-%m-%d")
        data = api("https://v3.football.api-sports.io/fixtures?date=" + date + "&timezone=Europe/Rome")
        for fx in data[:20]:
            hid=fx["teams"]["home"]["id"]; aid=fx["teams"]["away"]["id"]
            hs=get_stats(hid); time.sleep(0.1)
            aws=get_stats(aid); time.sleep(0.1)
            if hs and aws and hs["avg"]>=2.5 and aws["avg"]>=2.0:
                home=fx["teams"]["home"]["name"]; away=fx["teams"]["away"]["name"]
                ora=fx["fixture"]["date"][11:16]
                msg+= ora + " " + home + " vs " + away + " -> OVER 0.5 PT\n"
    tg(msg, cid, True)

def run_preparati(cid=None):
    msg = "PREPARATI E SEGNA - STA PER SEGNARE\n\n"
    data = api("https://v3.football.api-sports.io/fixtures?live=all")
    for fx in data[:15]:
        home=fx["teams"]["home"]["name"]; away=fx["teams"]["away"]["name"]
        el=fx["fixture"]["status"]["elapsed"]
        gh=fx["goals"]["home"]; ga=fx["goals"]["away"]
        if el and el>=70 and gh==ga:
            msg+= str(el) + "' " + home + " " + str(gh) + "-" + str(ga) + " " + away + " -> GOAL IN ARRIVO\n"
    tg(msg, cid, True)

def media(lid, name):
    txt = name.upper() + " " + datetime.now(ITALY).strftime("%d/%m") + "\nGOAL MEDIA\n\n"
    teams = api("https://v3.football.api-sports.io/teams?league=" + str(lid) + "&season=2024")
    for t in teams[:12]:
        tid=t["team"]["id"]; tname=t["team"]["name"]
        st=get_stats(tid)
        if not st: continue
        txt+= tname + ": Med " + str(round(st["avg"],2)) + " GF " + str(st["gf"]) + " BTTS " + str(int(st["btts"]*100)) + "%\n"
        time.sleep(0.15)
    return txt

# --- ROBA NUOVA 33 ---

def pronostico(hid, aid):
    hs=get_stats(hid); time.sleep(0.15)
    aws=get_stats(aid); time.sleep(0.15)
    if not hs or not aws: return "1X"
    pick="1X"
    if hs["uh"]>=4 and aws["ua"]<=2: pick="1X"
    elif aws["ua"]>=4 and hs["uh"]<=2: pick="X2"
    elif hs["win"]>0.6 and aws["win"]<0.3: pick="1"
    elif aws["win"]>0.6 and hs["win"]<0.3: pick="2"
    extra=""
    if (hs["btts"]+aws["btts"])/2>=0.6: extra=" + GOAL"
    media_g=(hs["avg"]+aws["avg"])/2
    if media_g>=2.8: extra+=" + OVER 1.5"
    elif media_g<=1.8: extra+=" + UNDER 3.5"
    return pick+extra

def run_bolla(cid=None):
    sel=[]
    for paese, lid in TOP33.items():
        for d in range(0,15):
            date=(datetime.now(ITALY)+timedelta(days=d)).strftime("%Y-%m-%d")
            data=api("https://v3.football.api-sports.io/fixtures?date=" + date + "&league=" + str(lid) + "&season=2024")
            if data:
                fx=data[0]
                home=fx["teams"]["home"]["name"]; away=fx["teams"]["away"]["name"]
                hid=fx["teams"]["home"]["id"]; aid=fx["teams"]["away"]["id"]
                fdate=fx["fixture"]["date"][:10]; ora=fx["fixture"]["date"][11:16]
                prono=pronostico(hid,aid)
                sel.append(fdate + " " + ora + " " + home + " vs " + away + " -> " + prono + " [" + paese + "]")
                break
        if len(sel)>=33: break
    msg="BOLLA EUROPA 33 NAZIONI\n" + str(len(sel)) + " partite\n\n"
    for i,m in enumerate(sel): msg+=str(i+1)+". "+m+"\n"
    tg(msg[:4000],cid,True)
    if len(msg)>4000: tg(msg[4000:],cid,True)

def run_doppia(cid=None):
    out=[]
    date=datetime.now(ITALY).strftime("%Y-%m-%d")
    data=api("https://v3.football.api-sports.io/fixtures?date=" + date + "&timezone=Europe/Rome")
    for fx in data[:20]:
        hid=fx["teams"]["home"]["id"]; aid=fx["teams"]["away"]["id"]
        home=fx["teams"]["home"]["name"]; away=fx["teams"]["away"]["name"]
        ora=fx["fixture"]["date"][11:16]
        prono=pronostico(hid,aid)
        out.append(ora + " " + home + " vs " + away + " -> " + prono)
    msg="DOPPIA 90% + GOAL\n\n"
    for i,m in enumerate(out): msg+=str(i+1)+". "+m+"\n"
    tg(msg,cid,True)

def poll():
    global last_id
    try: requests.get("https://api.telegram.org/bot"+BOT+"/deleteWebhook?drop_pending_updates=true", timeout=10)
    except: pass
    while True:
        try:
            base="https://api.telegram.org/bot"+BOT
            r=requests.get(base+"/getUpdates?offset="+str(last_id+1)+"&timeout=20", timeout=35).json()
            if r.get("ok"):
                for u in r.get("result", []):
                    last_id=u["update_id"]
                    txt=(u.get("message",{}).get("text") or "").strip()
                    low=txt.lower()
                    cid=u.get("message",{}).get("chat",{}).get("id")
                    if "live"==low: run_live(cid)
                    elif "ripartite" in low: run_ripartite(cid)
                    elif "primo tempo" in low: run_primo_tempo(cid)
                    elif "preparati" in low: run_preparati(cid)
                    elif "doppia" in low: run_doppia(cid)
                    elif "bolla" in low: run_bolla(cid)
                    elif "status" in low: tg("BOT V63 COMPLETO OK - TUTTA ROBA TUA C'E",cid,True)
                    else:
                        for k in LEAGUES:
                            if k.lower()==low: tg(media(LEAGUES[k],k),cid,True)
        except: time.sleep(5)
        time.sleep(2)

threading.Thread(target=poll, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), use_reloader=False)
