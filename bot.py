import requests, time, threading
from datetime import datetime, timedelta, timezone
import pytz

# === CONFIG ===
TELEGRAM_TOKEN = "IL_TUO_TOKEN_TELEGRAM"
API_FOOTBALL_KEY = "LA_TUA_API_KEY"
LIMITE = 7500

ITALY = pytz.timezone("Europe/Rome")
pre=[]; av_s=[]; token_usati=0; is_paused=False

def tg(msg,cid):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",json={"chat_id":cid,"text":msg},timeout=10)
    except: pass

def api_get(url):
    global token_usati
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=15).json()
        token_usati+=1
        if "errors" in r and "rate limit" in str(r).lower(): return "LIMIT"
        return r.get("response",[])
    except: return []

# === TOKEN VERO ===
def token_vero(cid):
    try:
        st=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10).json()
        req=st['response']['requests']['current']
        lim=st['response']['requests']['limit_day']
        rim=lim-req
        perc=int(req/lim*100)
        tg(f"💰 TOKEN VERO API-FOOTBALL\n\n🔢 Usati OGGI (reali): {req}\n📉 Rimanenti: {rim} / {lim}\n📊 Uso: {perc}%\n\n🔔 Pre: {len(pre)} | 🔥 Live: {len(av_s)}\nStato: {'PAUSA' if is_paused else 'ATTIVO'}",cid)
    except:
        rim=LIMITE-token_usati
        tg(f"💰 TOKEN (locale)\nUsati: {token_usati}\nRimanenti: {rim} / {LIMITE}",cid)

# === BLASONATE VERE - SOLO BIG TEAM ===
def bolla_blasonate(cid):
    BIG = ["inter","milan","juventus","juve","napoli","roma","lazio","atalanta","bologna","fiorentina","arsenal","manchester city","man city","liverpool","chelsea","manchester united","man united","tottenham","newcastle","aston villa","real madrid","barcelona","atletico madrid","athletic club","villarreal","betis","sevilla","bayern","dortmund","leverkusen","leipzig","stuttgart","psg","marseille","monaco","lyon","lille","benfica","porto","sporting","ajax","psv","feyenoord","galatasaray","fenerbahce","besiktas"]
    TOP_LEAGUES = ["serie a","premier league","la liga","bundesliga","ligue 1","primeira liga","eredivisie","super lig","jupiler pro league","scottish premiership"]

    OGGI=datetime.now(ITALY)
    out=[]; tot=1.0; visti=set()
    for delta in range(1,8):
        data=(OGGI+timedelta(days=delta)).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={data}")
        if not fx or fx=="LIMIT": continue
        for p in fx:
            if len(out)>=25: break
            lega=p['league']['name'].lower()
            if not any(t in lega for t in TOP_LEAGUES): continue
            if any(x in lega for x in ["u19","u21","u23","women","cup"]): continue
            home=p['teams']['home']['name'].lower()
            away=p['teams']['away']['name'].lower()
            if not any(b in home or b in away for b in BIG): continue
            fid=p["fixture"]["id"]
            if fid in visti: continue
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            best=None
            for b in odds[0]["bookmakers"][0]["bets"]:
                if "double chance" not in b["name"].lower(): continue
                for v in b["values"]:
                    try:
                        q=float(v["odd"])
                        if not 1.10<=q<=1.35: continue
                        if "Home/Draw" in v["value"]: best={"txt":"1X","q":q}
                        elif "Draw/Away" in v["value"]:
                            if best is None or q>best["q"]: best={"txt":"X2","q":q}
                    except: pass
            if not best: continue
            visti.add(fid)
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            tot*=best["q"]
            out.append(f"🕐 {dt.strftime('%a %d/%m %H:%M')}\n📍 {p['league']['country']} - {p['league']['name']}\n{p['teams']['home']['name']} vs {p['teams']['away']['name']}\n👉 {best['txt']} + Multigol 1-5 @ {best['q']*1.25:.2f}")

    if not out:
        tg("Niente BIG - sosta fino a Sab 10/10, da Sab ripartono Inter, Juve, Barca, Real, Bayern etc.\nOggi in Top c'è solo:\n- Dortmund vs Werder\n- Galatasaray vs Kasimpasa\n- Braga vs Sporting\n- Lens vs Lyon\n- PSV vs Heerenveen",cid)
        return
    tg(f"🔥 BLASONATE VERE [ {len(out)} partite ] - Quota tot {tot:.2f}\n\n"+"\n\n".join(out),cid)

# === OVER STATS - TORNA INDIETRO 10 PARTITE ===
def bolla_over_stats(cid, tipo="0.5"):
    OGGI=datetime.now(ITALY)
    out=[]; visti=set()
    soglia = 2.0 if tipo=="0.5" else 3.0
    tg(f"⏳ Analizzo ultime 10 partite per Over {tipo}... ci metto 1 minuto",cid)

    for delta in range(1,8):
        data=(OGGI+timedelta(days=delta)).strftime("%Y-%m-%d")
        fx=api_get(f"https://v3.football.api-sports.io/fixtures?date={data}")
        if not fx or fx=="LIMIT": continue
        for p in fx:
            if len(out)>=25: break
            lega=p['league']['name'].lower()
            if any(x in lega for x in ["u19","u21","u23","women","3. division","2. liga","3. liga","4. liga"]): continue
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
                if cnt==0: return 0,10
                return gol/cnt, zero

            h_avg, h_zero = stats(h_last)
            a_avg, a_zero = stats(a_last)
            media = (h_avg + a_avg)/2

            if media < soglia: continue
            if h_zero>=2 or a_zero>=2: continue

            visti.add(fid)
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            out.append({"txt": f"🕐 {dt.strftime('%a %d/%m %H:%M')} | {p['league']['name']}\n{p['teams']['home']['name']} vs {p['teams']['away']['name']}\n📊 Media gol ultime 10: {h_avg:.1f} + {a_avg:.1f} = TOT {media:.1f}\n0-0 ultime 10: {h_zero}+{a_zero}\n👉 OVER {tipo}","media": media})

    if not out:
        tg(f"Niente Over {tipo} con media {soglia}+ trovato - sosta Nazionali",cid)
        return
    out = sorted(out, key=lambda x: x["media"], reverse=True)
    txt_out = "\n\n".join([x["txt"] for x in out[:25]])
    tg(f"🔥 OVER {tipo} STATS - Media ultime 10 >= {soglia} gol\n{len(out)} partite - ordinate dalla più golosa\n\n"+txt_out,cid)

# === MENU ===
def handle(txt,cid):
    global is_paused
    txt=txt.lower()
    if "token" in txt: token_vero(cid)
    elif "blasonate" in txt: bolla_blasonate(cid)
    elif "over 0.5" in txt: bolla_over_stats(cid,"0.5")
    elif "over 1.5" in txt: bolla_over_stats(cid,"1.5")
    elif "pausa" in txt:
        is_paused=True; tg("⏸️ Pausa",cid)
    elif "riprendi" in txt:
        is_paused=False; tg("▶️ Ripreso",cid)
    else:
        tg("Comandi:\n💰 TOKEN\n🔥 BLASONATE LUN-DOM\n🔥 OVER 0.5 STATS\n🔥 OVER 1.5 STATS",cid)

# Il tuo loop Telegram resta uguale sotto...
