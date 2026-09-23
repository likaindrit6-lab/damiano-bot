import os, time, requests, json
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")
FILE = "sent.json"

def load():
    try:
        if os.path.exists(FILE):
            with open(FILE,"r") as f:
                d=json.load(f)
                return set(d.get("sent",[])), d.get("scores",{}), set(d.get("seguite",[])), d.get("last_gg",-1)
    except: pass
    return set(), {}, set(), -1

def save(s_set, sc_dict, seg_set, last_gg):
    try:
        with open(FILE,"w") as f:
            json.dump({"sent":list(s_set),"scores":sc_dict,"seguite":list(seg_set),"last_gg":last_gg},f)
    except: pass

sent, last_scores, seguite, last_gg_hour = load()
schedine_fatte = False

def tg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        print(f"Errore TG: {e}")

def api_get(url):
    h = {"x-apisports-key": API_KEY}
    try:
        r = requests.get(url, headers=h, timeout=20).json()
        return r.get("response", [])
    except: return []

def get_live(): return api_get("https://v3.football.api-sports.io/fixtures?live=all")
def get_stats(fid): return api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
def get_events(fid): return api_get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}")
def get_today():
    tz = pytz.timezone("Europe/Rome")
    today = datetime.now(tz).strftime("%Y-%m-%d")
    return api_get(f"https://v3.football.api-sports.io/fixtures?date={today}")

def get_last5_avg(tid):
    d=api_get(f"https://v3.football.api-sports.io/fixtures?team={tid}&last=5")
    if len(d)<3: return 0
    tot=0
    for m in d:
        tot+=(m["goals"]["home"] or 0)+(m["goals"]["away"] or 0)
    return tot/len(d)

def get_quote(fid):
    try:
        odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
        if not odds: return 99
        for b in odds[0].get("bookmakers",[]):
            for bet in b.get("bets",[]):
                if bet["id"]==1:
                    vals=[float(v["odd"]) for v in bet["values"] if v.get("odd")]
                    if vals: return min(vals)
    except: pass
    return 99

def fmt(m):
    return f"{m['league']['country']} - {m['league']['name']} - {m['teams']['home']['name']} vs {m['teams']['away']['name']}"

print("BOT V6.1 - CON OVER 1.5")
tg("✅ <b>BOT V6.1 ATTIVO</b>\n- Live Calda/Morta/Corner/Rosso\n- Gol solo se seguita\n- Schedina 10:00 con Over 1.5 (5 vecchie)\n- GG ogni 2h")

while True:
    try:
        tz=pytz.timezone("Europe/Rome")
        now=datetime.now(tz)

        if now.hour==0 and now.minute<4:
            sent.clear(); last_scores.clear(); seguite.clear()
            save(sent,last_scores,seguite,-1)
            schedine_fatte=False; last_gg_hour=-1

        # SCHEDINE 10:00 - ENTRAMBE
        if now.hour==10 and now.minute<5 and not schedine_fatte:
            fixtures=get_today()
            ns=[f for f in fixtures if f["fixture"]["status"]["short"]=="NS"]
            if len(ns)>=3:
                # SCHEDINA 1 - QUOTA 1.60/1.80
                quotate=[]
                for f in ns[:20]:
                    q=get_quote(f["fixture"]["id"])
                    quotate.append((q,f))
                    time.sleep(0.5)
                quotate.sort(key=lambda x:x[0])
                s1=[x[1] for x in quotate[:3] if x[0]!=99]
                if len(s1)<3: s1=ns[:3]
                txt1="📋 <b>SCHEDINA 1 - QUOTA 1.60/1.80</b>\n\n"
                for x in s1: txt1+=f"• {fmt(x)} - {x['fixture']['date'][11:16]}\n"
                tg(txt1); time.sleep(1)

                # SCHEDINA 2 - OVER 1.5 IN BASE ALLE 5 VECCHIE
                sel=[]
                tg("⏳ <b>Calcolo Over 1.5 in corso... controllo ultime 5 partite</b>")
                for f in ns:
                    if len(sel)>=20: break
                    try:
                        avg_home=get_last5_avg(f['teams']['home']['id'])
                        time.sleep(0.4)
                        avg_away=get_last5_avg(f['teams']['away']['id'])
                        time.sleep(0.4)
                        media=(avg_home+avg_away)/2
                        if media>=1.6:
                            sel.append((f,media))
                    except: continue

                if sel:
                    txt2=f"📊 <b>SCHEDINA 2 - OVER 1.5 - {len(sel)} partite (media gol ultime 5 >1.6)</b>\n\n"
                    for x,media in sel:
                        txt2+=f"• {fmt(x)} - {x['fixture']['date'][11:16]} (media {media:.1f})\n"
                    tg(txt2)
                else:
                    tg("📊 <b>SCHEDINA 2 OVER 1.5:</b> Oggi nessuna partita con media >1.6 nelle ultime 5")
            schedine_fatte=True

        # GG OGNI 2 ORE
        if now.minute<4 and now.hour%2==0 and now.hour>=12 and now.hour<=22 and now.hour!=last_gg_hour:
            fixtures=get_today()
            ns=[f for f in fixtures if f["fixture"]["status"]["short"]=="NS"]
            cand=[f for f in ns if not any(x in f["league"]["name"] for x in ["U19","U18","U17","Friendly"])][:10]
            if len(cand)>=2:
                top=cand[:3]
                txt=f"⚽ <b>GOL GOL - TOP {len(top)} - ORE {now.hour}:00</b>\n\n"
                for f in top: txt+=f"• {fmt(f)} - {f['fixture']['date'][11:16]}\n"
                tg(txt)
            last_gg_hour=now.hour; save(sent,last_scores,seguite,last_gg_hour)

        # LIVE
        lives=get_live()
        for m in lives:
            fid=str(m["fixture"]["id"])
            minute=m["fixture"]["status"]["elapsed"] or 0
            gh=m["goals"]["home"] or 0; ga=m["goals"]["away"] or 0
            score=f"{gh}-{ga}"
            if any(x in m["league"]["name"] for x in ["U19","U18","U17","Friendly","Club Friendly"]): continue
            full=fmt(m)
            stats=get_stats(int(fid))
            shots_on=corners=0
            for ts in stats:
                for s in ts.get("statistics",[]):
                    t=s.get("type",""); v=s.get("value") or 0
                    if not isinstance(v,int): continue
                    if t=="Shots on Goal": shots_on+=v
                    if "Corner" in t: corners+=v
            if fid in last_scores:
                ogh,oga=last_scores[fid]
                if (gh!=ogh or ga!=oga) and fid in seguite:
                    tg(f"⚽ <b>GOL! {score} al {minute}'</b>\n{full}\nEra {ogh}-{oga}")
                if gh!=ogh or ga!=oga:
                    last_scores[fid]=(gh,ga); save(sent,last_scores,seguite,last_gg_hour)
            else: last_scores[fid]=(gh,ga)
            is_valid=(gh==0 and ga==0) or (gh==1 and ga==0) or (gh==0 and ga==1)
            if 5<minute<60 and is_valid:
                if f"tiri_{fid}" not in sent and shots_on>=6:
                    tg(f"🔥 <b>CALDA {score} al {minute}' - {shots_on} tiri</b>\n{full}"); sent.add(f"tiri_{fid}"); seguite.add(fid); save(sent,last_scores,seguite,last_gg_hour)
                if f"corner_{fid}" not in sent and corners>=8:
                    tg(f"🚩 <b>CORNER {corners} al {minute}' - {score}</b>\n{full}"); sent.add(f"corner_{fid}"); seguite.add(fid); save(sent,last_scores,seguite,last_gg_hour)
                if f"morta_{fid}" not in sent and minute>=30 and shots_on<=3:
                    tg(f"💀 <b>MORTA {score} al {minute}' - {shots_on} tiri</b>\n{full}"); sent.add(f"morta_{fid}"); seguite.add(fid); save(sent,last_scores,seguite,last_gg_hour)
            if f"red_{fid}" not in sent and minute<70:
                events=get_events(int(fid))
                for ev in events:
                    if ev["type"]=="Card" and "Red" in str(ev.get("detail","")):
                        rmin=ev["time"]["elapsed"] or 0
                        if 0<rmin<70:
                            tg(f"🟥 <b>ROSSO al {rmin}' (ora {minute}' {score})</b>\n{full}"); sent.add(f"red_{fid}"); save(sent,last_scores,seguite,last_gg_hour); break
            time.sleep(1)
        time.sleep(90)
    except Exception as e:
        print(f"ERR {e}"); time.sleep(30)
