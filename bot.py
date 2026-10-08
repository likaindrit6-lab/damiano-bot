import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0

try:
    base="https://api.telegram.org/bot"+BOT_TOKEN
    requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    s="PAUSA 0 CONSUMI" if is_paused else "ATTIVO"
    return "BOT V30.7 FIX QUOTES - "+s,200

def run_flask():
    from waitress import serve
    p=int(os.environ.get("PORT",10000))
    serve(app,host='0.0.0.0',port=p)
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({
    "keyboard":[
        ["\U0001F7E2 ACCENDI","\U0001F534 SPEGNI"],
        ["\U0001F3C6 BLASONATE LUN-SAB","\u26BD PARTITE OGGI"],
        ["\u2B07\uFE0F UNDER","\U0001F4CA TOKEN"]
    ],
    "resize_keyboard":True,"is_persistent":True
})

def tg(m,chat_id=None,con_tastiera=False):
    try:
        cid=chat_id if chat_id else CHAT_ID
        url="https://api.telegram.org/bot"+BOT_TOKEN+"/sendMessage"
        payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
        if con_tastiera:
            payload["reply_markup"]=TASTIERA_JSON
        if len(m) > 3900:
            for i in range(0, len(m), 3900):
                payload["text"]=m[i:i+3900]
                if i>0:
                    payload.pop("reply_markup",None)
                requests.post(url,json=payload,timeout=25)
                time.sleep(0.5)
        else:
            requests.post(url,json=payload,timeout=25)
    except:
        pass

def api_get(url):
    if is_paused:
        return []
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
        if r.status_code==429:
            return "LIMIT"
        return r.json().get("response",[])
    except:
        return []

def get_token_status():
    try:
        r=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10)
        d=r.json()["response"]["requests"]
        cur=d['current']
        lim=d['limit_day']
        rim=lim-cur
        return "TOKEN "+str(cur)+"/"+str(lim)+" Rimasti:"+str(rim)
    except Exception as e:
        return "Errore token: "+str(e)

def get_flag(p):
    m={"Italy":"\U0001F1EE\U0001F1F9","England":"\U0001F1EC\U0001F1E7","Spain":"\U0001F1EA\U0001F1F8","Germany":"\U0001F1E9\U0001F1EA","France":"\U0001F1EB\U0001F1F7","Portugal":"\U0001F1F5\U0001F1F9","Netherlands":"\U0001F1F3\U0001F1F1","Belgium":"\U0001F1E7\U0001F1EA","Turkey":"\U0001F1F9\U0001F1F7","Brazil":"\U0001F1E7\U0001F1F7","Argentina":"\U0001F1E6\U0001F1F7","Iran":"\U0001F1EE\U0001F1F7"}
    return m.get(p,"\U0001F3F3\uFE0F")

def is_ok_league(l,c):
    s=(l+" "+c).lower()
    bad=["women","female","u19","u21","u23","reserve","youth","futsal","amateur"]
    for x in bad:
        if x in s:
            return False
    return True

def is_blasonata(l,c):
    if not is_ok_league(l,c):
        return False
    ln=l.lower()
    k=["serie a","serie b","premier league","championship","laliga","la liga","segunda","bundesliga","ligue 1","ligue 2","primeira","eredivisie","pro league","super lig","brasileiro","liga profesional"]
    for x in k:
        if x in ln:
            return True
    return False

def get_lun_sab():
    oggi=datetime.now(ITALY)
    lun=oggi-timedelta(days=oggi.weekday())
    sab=lun+timedelta(days=5)
    return lun,sab

def crea_blasonate_lun_sab():
    try:
        d1,d2=get_lun_sab()
        label="LUN-SAB "+d1.strftime("%d/%m")+"->"+d2.strftime("%d/%m")
        tutte=[]
        for i in range((d2-d1).days+1):
            giorno=(d1+timedelta(days=i)).strftime("%Y-%m-%d")
            fx=api_get("https://v3.football.api-sports.io/fixtures?date="+giorno)
            if fx=="LIMIT":
                continue
            fx=[f for f in fx if is_blasonata(f['league']['name'],f['league']['country'])]
            tutte.extend(fx)
            time.sleep(0.2)
        if not tutte:
            return "Nessuna blasonata "+label+" - sosta nazionali"
        cand=[]
        for p in sorted(tutte,key=lambda x:x["fixture"]["timestamp"]):
            if len(cand)>=80:
                break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            home=p['teams']['home']['name']
            away=p['teams']['away']['name']
            paese=p['league']['country']
            lega=p['league']['name']
            flag=get_flag(paese)
            ora=dt.strftime("%d/%m %H:%M")
            odds=api_get("https://v3.football.api-sports.io/odds?fixture="+str(fid))
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"):
                continue
            best=None
            for b in odds[0]["bookmakers"]:
                for bet in b["bets"]:
                    bn=bet["name"].lower()
                    if "double chance" in bn or "multigoal" in bn or "multi goals" in bn:
                        for v in bet["values"]:
                            try:
                                q=float(v["odd"])
                                if 1.08 <= q <= 1.45:
                                    if not best or q < best["q"]:
                                        best={"q":q,"m":bet["name"],"e":v["value"]}
                            except:
                                pass
            if not best:
                continue
            qenc=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
            link="https://www.google.com/search?q="+qenc+"&btnI=1"
            qenc2=urllib.parse.quote_plus(home+" "+away+" site:planetwin365.it")
            link2="https://www.google.com/search?q="+qenc2+"&btnI=1"
            prob=int((1/best["q"])*100)
            if "Double" in best["m"]:
                tipo="DOPPIA "+best["e"]
            else:
                tipo="MULTIGOL 1-5 "+best["e"]
            txt=flag+" "+paese.upper()+" | "+ora+" | "+lega+"\n"+home+" vs "+away+"\n-> "+tipo+" @ "+str(best["q"])+" ("+str(prob)+"%)\n<a href='"+link+"'>BET365</a> | <a href='"+link2+"'>PLANETWIN365</a>"
            cand.append({"q":best["q"],"txt":txt})
        if not cand:
            return "0 blasonate "+label
        cand=sorted(cand,key=lambda x:x["q"])
        picks=cand[:25]
        tot=1
        for x in picks:
            tot*=x["q"]
        body="\n\n".join([p["txt"] for p in picks])
        return "BLASONATE "+label+" - "+str(len(picks))+" PARTITE - Quota "+str(round(tot,2))+"\n\n"+body+"\n\nTOT "+str(round(tot,2))
    except Exception as e:
        return "Errore blasonate: "+str(e)

def crea_partite_oggi():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fx=api_get("https://v3.football.api-sports.io/fixtures?date="+OGGI)
        if fx=="LIMIT":
            return "Limite API - aspetta 1h"
        fx=[f for f in fx if is_ok_league(f['league']['name'],f['league']['country'])]
        fx=sorted(fx,key=lambda x:x["fixture"]["timestamp"])
        cand=[]
        for p in fx:
            if len(cand)>=100:
                break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY):
                continue
            home=p['teams']['home']['name']
            away=p['teams']['away']['name']
            paese=p['league']['country']
            lega=p['league']['name']
            flag=get_flag(paese)
            ora=dt.strftime("%H:%M")
            odds=api_get("https://v3.football.api-sports.io/odds?fixture="+str(fid))
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"):
                continue
            best=None
            for b in odds[0]["bookmakers"]:
                for bet in b["bets"]:
                    bn=bet["name"].lower()
                    if "double chance" in bn or "multigoal" in bn:
                        for v in bet["values"]:
                            try:
                                q=float(v["odd"])
                                if 1.08 <= q <= 1.35:
                                    if not best or q < best["q"]:
                                        best={"q":q,"m":bet["name"],"e":v["value"]}
                            except:
                                pass
            if not best:
                continue
            qenc=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
            link="https://www.google.com/search?q="+qenc+"&btnI=1"
            qenc2=urllib.parse.quote_plus(home+" "+away+" site:planetwin365.it")
            link2="https://www.google.com/search?q="+qenc2+"&btnI=1"
            prob=int((1/best["q"])*100)
            if "Double" in best["m"]:
                tipo="DOPPIA "+best["e"]
            else:
                tipo="MULTIGOL "+best["e"]
            txt=flag+" "+paese.upper()+" | "+ora+" | "+lega+"\n"+home+" vs "+away+"\n-> "+tipo+" @ "+str(best["q"])+" ("+str(prob)+"%)\n<a href='"+link+"'>BET365</a> | <a href='"+link2+"'>PLANETWIN365</a>"
            cand.append({"q":best["q"],"txt":txt})
        if not cand:
            return "0 partite oggi "+OGGI
        cand=sorted(cand,key=lambda x:x["q"])
        picks=cand[:15]
        tot=1
        for x in picks:
            tot*=x["q"]
        body="\n\n".join([p["txt"] for p in picks])
        return "PARTITE OGGI "+OGGI+" - 90% - "+str(len(picks))+" partite - "+str(round(tot,2))+"\n\n"+body+"\n\nTOT "+str(round(tot,2))
    except Exception as e:
        return "Errore oggi: "+str(e)

def crea_under():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fx=api_get("https://v3.football.api-sports.io/fixtures?date="+OGGI)
        fx=[f for f in fx if is_ok_league(f['league']['name'],f['league']['country'])]
        picks=[]
        for p in fx:
            if len(picks)>=10:
                break
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < datetime.now(ITALY):
                continue
            home=p['teams']['home']['name']
            away=p['teams']['away']['name']
            paese=p['league']['country']
            lega=p['league']['name']
            flag=get_flag(paese)
            ora=dt.strftime("%H:%M")
            odds=api_get("https://v3.football.api-sports.io/odds?fixture="+str(fid))
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"):
                continue
            for b in odds[0]["bookmakers"]:
                for bet in b["bets"]:
                    if "Over/Under" in bet["name"]:
                        for v in bet["values"]:
                            if "Under 4.5" in v["value"]:
                                try:
                                    q=float(v["odd"])
                                    if 1.12 <= q <= 1.40:
                                        qenc=urllib.parse.quote_plus(home+" "+away+" site:bet365.it")
                                        link="https://www.google.com/search?q="+qenc+"&btnI=1"
                                        prob=int((1/q)*100)
                                        txt=flag+" "+paese.upper()+" | "+ora+" | "+lega+"\n"+home+" vs "+away+"\n-> UNDER 4.5 @ "+str(q)+" ("+str(prob)+"%)\n<a href='"+link+"'>BET365</a>"
                                        picks.append(txt)
                                except:
                                    pass
        if not picks:
            return "0 UNDER oggi"
        body="\n\n".join(picks)
        return "UNDER 4.5 OGGI - "+str(len(picks))+" partite\n\n"+body
    except Exception as e:
        return "Errore under: "+str(e)

def poll_commands():
    global is_paused,last_update_id
    while True:
        try:
            base="https://api.telegram.org/bot"+BOT_TOKEN
            r=requests.get(base+"/getUpdates?offset="+str(last_update_id+1)+"&timeout=25",timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result",[]):
                    last_update_id=upd["update_id"]
                    txt=upd.get("message",{}).get("text","").lower()
                    chat=upd.get("message",{}).get("chat",{}).get("id")
                    if "spegni" in txt:
                        is_paused=True
                        tg("PAUSA 0 CONSUMI",chat,con_tastiera=True)
                    elif "accendi" in txt or "/start" in txt:
                        is_paused=False
                        tg("BOT V30.7 FIXATO - PRONTO",chat,con_tastiera=True)
                    elif "token" in txt:
                        tg(get_token_status(),chat,con_tastiera=True)
                    elif "lun-sab" in txt or "blasonate" in txt:
                        tg("Cerco BLASONATE LUN-SAB 20-25...",chat)
                        tg(crea_blasonate_lun_sab(),chat,con_tastiera=True)
                    elif "partite oggi" in txt or "oggi" in txt:
                        tg("Cerco PARTITE OGGI 90%...",chat)
                        tg(crea_partite_oggi(),chat,con_tastiera=True)
                    elif "under" in txt:
                        tg("Cerco UNDER 4.5...",chat)
                        tg(crea_under(),chat,con_tastiera=True)
        except:
            pass
        time.sleep(2)

threading.Thread(target=poll_commands,daemon=True).start()

while True:
    try:
        if is_paused:
            time.sleep(300)
            continue
        now=datetime.now(ITALY)
        if 0 <= now.hour < 10:
            time.sleep(600)
            continue
        time.sleep(180)
    except:
        time.sleep(15)
