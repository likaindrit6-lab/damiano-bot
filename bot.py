import requests, time, threading, os
from datetime import datetime, timedelta, timezone

# === CONFIG ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "IL_TUO_TOKEN_TELEGRAM")
API_FOOTBALL_KEY = os.environ.get("API_KEY", "LA_TUA_API_KEY")
CHAT_ID = int(os.environ.get("CHAT_ID", "0") or 0)
LIMITE = 7500

ITALY = timezone(timedelta(hours=2)) # Roma senza pytz - FIX
pre=[]; av_s=[]; token_usati=0; is_paused=False

def tg(msg,cid=CHAT_ID):
    try:
        for i in range(0, len(msg), 4000):
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          json={"chat_id":cid,"text":msg[i:i+4000]},timeout=10)
            time.sleep(0.3)
    except: pass

def api_get(url):
    global token_usati
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=15).json()
        token_usati+=1
        if "errors" in r and r["errors"]:
            if "limit" in str(r["errors"]).lower(): return "LIMIT"
        return r.get("response",[])
    except: return []

def token_vero(cid):
    try:
        st=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10).json()
        req=st['response']['requests']['current']
        lim=st['response']['requests']['limit_day']
        rim=lim-req
        perc=int(req/lim*100) if lim>0 else 0
        tg(f"💰 TOKEN VERO\nUsati: {req}\nRimanenti: {rim}/{lim} ({perc}%)\nPre: {len(pre)} Live: {len(av_s)}",cid)
    except:
        rim=LIMITE-token_usati
        tg(f"💰 TOKEN locale: {token_usati}\nRimanenti: {rim}/{LIMITE}",cid)

def bolla_blasonate(cid):
    BIG = ["inter","milan","juventus","juve","napoli","roma","lazio","atalanta","bologna","fiorentina","arsenal","manchester city","man city","liverpool","chelsea","manchester united","man united","tottenham","newcastle","aston villa","real madrid","barcelona","atletico madrid","athletic club","villarreal","betis","sevilla","bayern","dortmund","leverkusen","leipzig","stuttgart","psg","marseille","monaco","lyon","lille","benfica","porto","sporting","ajax","psv","feyenoord","galatasaray","fenerbahce","besiktas"]
    TOP_LEAGUES = ["serie a","premier league","la liga","bundesliga","ligue 1","primeira liga","eredivisie","super lig"]
    OGGI=datetime.now(ITALY)
    out=[]; tot=1.0; visti=set()
    tg("⏳ Cerco BLASONATE...",cid)
    for delta in range(0,8):
        data=(OGGI+timedelta(days=delta)).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={data}")
        if not fx or fx=="LIMIT": continue
        for p in fx:
            if len(out)>=25: break
            lega=p['league']['name'].lower()
            if not any(t in lega for t in TOP_LEAGUES): continue
            if any(x in lega for x in ["u19","u21","women"]): continue
            home=p['teams']['home']['name'].lower()
            away=p['teams']['away']['name'].lower()
            if not any(b in home or b in away for b in BIG): continue
            fid=p["fixture"]["id"]
            if fid in visti: continue
            visti.add(fid)
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            out.append(f"🕐 {dt.strftime('%a %d/%m %H:%M')} {p['league']['name']}\n{p['teams']['home']['name']} vs {p['teams']['away']['name']}\n👉 1X + Multigol 1-5")

    if not out:
        tg("Niente BIG - sosta fino a Sab 11/10",cid)
        return
    tg(f"🔥 BLASONATE VERE [{len(out)}]\n\n"+"\n\n".join(out),cid)

def bolla_over_stats(cid, tipo="0.5"):
    OGGI=datetime.now(ITALY)
    out=[]; visti=set()
    soglia = 2.0 if tipo=="0.5" else 2.8
    tg(f"⏳ Over {tipo} - analizzo ultime 10...",cid)
    for delta in range(0,8):
        data=(OGGI+timedelta(days=delta)).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={data}")
        if not fx or fx=="LIMIT": continue
        for p in fx:
            if len(out)>=25: break
            lega=p['league']['name'].lower()
            if any(x in lega for x in ["u19","u21","women","3. division","2. liga"]): continue
            fid=p["fixture"]["id"]
            if fid in visti: continue
            home_id=p['teams']['home']['id']
            away_id=p['teams']['away']['id']
            h_last=api_get(f"https://v3.football.api-sports.io/fixtures?team={home_id}&last=10")
            a_last=api_get(f"https://v3.football.api-sports.io/fixtures?team={away_id}&last=10")
            if not h_last or not a_last or len(h_last)<5: continue
            def stats(last):
                gol=0; zero=0; cnt=0
                for m in last:
                    gh=m['goals']['home']; ga=m['goals']['away']
                    if gh is None: continue
                    tot=gh+ga
                    gol+=tot; cnt+=1
                    if tot==0: zero+=1
                return (gol/cnt if cnt else 0), zero
            h_avg, h_zero = stats(h_last)
            a_avg, a_zero = stats(a_last)
            media = (h_avg + a_avg)/2
            if media < soglia: continue
            if h_zero>=2 or a_zero>=2: continue
            visti.add(fid)
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            out.append({"txt": f"🕐 {dt.strftime('%a %d/%m %H:%M')} {p['league']['name']}\n{p['teams']['home']['name']} vs {p['teams']['away']['name']}\nMedia 10: {media:.1f} gol\n👉 OVER {tipo}","media": media})

    if not out:
        tg(f"Niente Over {tipo}",cid)
        return
    out = sorted(out, key=lambda x: x["media"], reverse=True)
    txt_out = "\n\n".join([x["txt"] for x in out[:25]])
    tg(f"🔥 OVER {tipo} - {len(out)} partite\n\n"+txt_out,cid)

def handle(txt,cid):
    global is_paused
    t=txt.lower()
    if "token" in t: token_vero(cid)
    elif "blasonate" in t: threading.Thread(target=bolla_blasonate,args=(cid,)).start()
    elif "over 1.5" in t: threading.Thread(target=bolla_over_stats,args=(cid,"1.5")).start()
    elif "over 0.5" in t: threading.Thread(target=bolla_over_stats,args=(cid,"0.5")).start()
    else:
        tg("Comandi:\n💰 TOKEN\n🔥 BLASONATE LUN-DOM\n🔥 OVER 0.5 STATS\n🔥 OVER 1.5 STATS",cid)

def main():
    offset=0
    print("BOT V26.1 STARTATO - SENZA PYTZ")
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",params={"offset":offset,"timeout":30},timeout=35).json()
            for u in r.get("result",[]):
                offset=u["update_id"]+1
                msg=u.get("message",{})
                txt=msg.get("text","")
                cid=msg.get("chat",{}).get("id",CHAT_ID)
                if txt:
                    handle(txt,cid)
        except Exception as e:
            print("loop err",e)
            time.sleep(5)

if __name__=="__main__":
    main()
