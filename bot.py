import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")

ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
ultimo_gol={}
ultima_schedina_ora=-1
schedina_attiva=[]
schedina_notificata=set()
live_inviate=set()

if BOT_TOKEN:
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except: pass

app=Flask(__name__)
@app.route('/')
def home(): return "BOT V36 FULL VERDE",200
@app.route('/health')
def health(): return "OK",200

TASTIERA=json.dumps({"keyboard":[["ACCENDI","SPEGNI"],["BLASONATE LUN-DOM","PARTITE OGGI"],["SCHEDINA ORA","UNDER","TOKEN"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id or CHAT_ID
        if not BOT_TOKEN or not cid: return
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera: payload["reply_markup"]=TASTIERA
        if len(m)>3800:
            for i in range(0,len(m),3800):
                payload["text"]=m[i:i+3800]
                if i>0: payload.pop("reply_markup",None)
                requests.post(url,json=payload,timeout=15)
                time.sleep(0.3)
        else: requests.post(url,json=payload,timeout=15)
    except Exception as e: print(e,flush=True)

def api_get(url):
    if is_paused: return []
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=15)
        if r.status_code==429: return "LIMIT"
        return r.json().get("response",[])
    except: return []

def is_ok_league(l,c):
    s=(l+" "+c).lower()
    for x in ["women","female","u19","u21","u23","reserve","youth","futsal","amateur"]:
        if x in s: return False
    return True

def crea_schedina_oraria():
    global schedina_attiva, schedina_notificata
    try:
        fx=api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if fx=="LIMIT": return "Limite API"
        if not fx: return "Nessuna LIVE ora"
        cand=[]
        for p in fx:
            try:
                fid=p["fixture"]["id"]
                minute=p["fixture"]["status"]["elapsed"]
                if minute is None or minute<5 or minute>80: continue
                home=p['teams']['home']['name']
                away=p['teams']['away']['name']
                if " ii" in (home+away).lower(): continue
                if not is_ok_league(p['league']['name'],p['league']['country']): continue
                odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
                best=None
                for b in odds[0]["bookmakers"]:
                    for bet in b["bets"]:
                        if "double chance" in bet["name"].lower():
                            for v in bet["values"]:
                                if "home/away" in v["value"].lower() or v["value"].strip()=="12": continue
                                try:
                                    q=float(v["odd"])
                                    if 1.08 <= q <= 1.35:
                                        best={"q":q,"e":v["value"],"fid":fid,"home":home,"away":away}
                                except: pass
                if not best: continue
                txt=f"{minute}' {home} vs {away} | {best['e']} @ {best['q']}"
                cand.append({"q":best["q"],"txt":txt,"data":best})
            except: continue
        if len(cand)<2: return f"Poche LIVE ({len(cand)})"
        cand=sorted(cand,key=lambda x:x["q"])
        picks=[]; tot=1.0
        for c in cand:
            if tot>=1.6: break
            picks.append(c); tot*=c["q"]
            if tot>1.9: tot/=c["q"]; picks.pop()
        if tot<1.55: return "Non riesco a fare 1.6 ora"
        schedina_attiva=[pk["data"] for pk in picks]
        schedina_notificata.clear()
        body="\n\n".join([p["txt"] for p in picks])
        return f"🔥 SCHEDINA ORARIA LIVE Quota {tot:.2f} - 90%\nTi avviso GOL e VINCENTE!\n\n{body}\n\nTOT {tot:.2f}"
    except Exception as e: return f"Errore: {e}"

def crea_blasonate():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        big=["milan","inter","juventus","juve","napoli","roma","lazio","atalanta","real madrid","barcelona","atletico","psg","bayern","dortmund","manchester city","man city","manchester united","liverpool","chelsea","arsenal","benfica","porto"]
        cand=[]
        for p in fx:
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            t=(home+" "+away).lower()
            if not any(b in t for b in big): continue
            fid=p["fixture"]["id"]
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            best=None
            for b in odds[0]["bookmakers"]:
                for bet in b["bets"]:
                    if "double chance" in bet["name"].lower():
                        for v in bet["values"]:
                            if "12" in v["value"]: continue
                            try:
                                q=float(v["odd"])
                                if 1.12 <= q <= 1.50: best={"q":q,"e":v["value"]}
                            except: pass
            if not best: continue
            cand.append(f"{home} vs {away} | {best['e']} @ {best['q']}")
        if not cand: return "Nessuna blasonata oggi"
        return "🔵 BLASONATE OGGI\n\n" + "\n".join(cand[:15])
    except Exception as e: return str(e)

def monitor_live():
    while True:
        try:
            if is_paused: time.sleep(120); continue
            fx=api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if not fx or fx=="LIMIT": time.sleep(90); continue
            for p in fx:
                fid=p["fixture"]["id"]
                minute=p["fixture"]["status"]["elapsed"]
                if minute is None or minute>90: continue
                if p["fixture"]["status"]["short"] not in ["1H","HT","2H"]: continue
                home=p['teams']['home']['name']
                away=p['teams']['away']['name']
                gh=p['goals']['home']; ga=p['goals']['away']
                tot_gol=gh+ga
                last=ultimo_gol.get(fid,-1)
                if last!=-1 and tot_gol>last:
                    key=f"gol-{fid}-{tot_gol}"
                    if key not in live_inviate:
                        in_sched=any(s["fid"]==fid for s in schedina_attiva)
                        if in_sched:
                            tg(f"⚽ GOL NELLA TUA SCHEDINA! {minute}' {home} {gh}-{ga} {away}",con_tastiera=True)
                        else:
                            tg(f"⚽ GOL! {minute}' {home} {gh}-{ga} {away}",con_tastiera=True)
                        live_inviate.add(key)
                ultimo_gol[fid]=tot_gol
                for s in schedina_attiva:
                    if s["fid"]!=fid: continue
                    e_low=s["e"].lower()
                    vincente=False
                    if "home/draw" in e_low and gh>=ga: vincente=True
                    if "draw/away" in e_low and ga>=gh: vincente=True
                    if vincente and 80<=minute<=89 and f"quasi-{fid}" not in schedina_notificata:
                        tg(f"✅ SCHEDINA QUASI VINCENTE! {minute}' {home} {gh}-{ga} {away} - E' VERDE!",con_tastiera=True)
                        schedina_notificata.add(f"quasi-{fid}")
                    if minute>=90 and f"ft-{fid}" not in schedina_notificata:
                        if vincente: tg(f"✅✅ SCHEDINA CHIUSA VINCENTE! {home} {gh}-{ga} {away}",con_tastiera=True)
                        else: tg(f"❌ SCHEDINA PERSA {home} {gh}-{ga} {away}",con_tastiera=True)
                        schedina_notificata.add(f"ft-{fid}")
                if len(live_inviate)>400: live_inviate.clear()
            time.sleep(90)
        except: time.sleep(60)

def schedina_loop():
    global ultima_schedina_ora
    while True:
        try:
            if is_paused: time.sleep(60); continue
            now=datetime.now(ITALY)
            if now.hour!=ultima_schedina_ora and now.minute>=2:
                tg(crea_schedina_oraria(),con_tastiera=True)
                ultima_schedina_ora=now.hour
                time.sleep(3600)
            else: time.sleep(30)
        except: time.sleep(60)

def poll_commands():
    global is_paused,last_update_id
    while True:
        try:
            if not BOT_TOKEN: time.sleep(10); continue
            r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=20",timeout=30).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    txt=upd.get("message",{}).get("text","").lower()
                    chat=upd.get("message",{}).get("chat",{}).get("id")
                    if not txt: continue
                    if "spegni" in txt: is_paused=True; tg("PAUSA 0 consumi",chat,True)
                    elif "accendi" in txt or "/start" in txt: is_paused=False; tg("BOT V36 FULL VERDE - LIVE + ORARIA + GOL + VINCENTE + BLASONATE!",chat,True)
                    elif "schedina ora" in txt: tg(crea_schedina_oraria(),chat,True)
                    elif "blasonate" in txt or "lun-dom" in txt or "partite oggi" in txt: tg(crea_blasonate(),chat,True)
                    elif "token" in txt:
                        s=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10).json()
                        d=s["response"]["requests"]
                        tg(f"TOKEN {d['current']}/{d['limit_day']} Rimasti {d['limit_day']-d['current']}",chat,True)
        except Exception as e: print(e,flush=True)
        time.sleep(2)

threading.Thread(target=monitor_live,daemon=True).start()
threading.Thread(target=schedina_loop,daemon=True).start()
threading.Thread(target=poll_commands,daemon=True).start()

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0',port=port)
