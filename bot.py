
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
                return set(d.get("sent",[])), d.get("scores",{}), set(d.get("seguite",[]))
    except: pass
    return set(), {}, set()
def save(s_set, sc_dict, seg_set):
    try:
        with open(FILE,"w") as f: json.dump({"sent": list(s_set), "scores": sc_dict, "seguite": list(seg_set)}, f)
    except: pass

sent, last_scores, seguite = load()
schedine_fatte = False

def tg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)

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
def get_last5_avg(team_id):
    data = api_get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5")
    if len(data) < 2: return 0
    tot = sum((m["goals"]["home"] or 0)+(m["goals"]["away"] or 0) for m in data)
    return tot / len(data)
def get_odds_quote(fid):
    # Prova a prendere quota 1X2 più bassa
    try:
        odds = api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
        if not odds: return 99
        for book in odds[0].get("bookmakers",[]):
            for bet in book.get("bets",[]):
                if bet["id"]==1: # 1X2
                    vals = [float(v["odd"]) for v in bet["values"] if v["odd"]]
                    if vals: return min(vals)
    except: pass
    return 99

def format_match(m):
    country = m["league"]["country"]
    league = m["league"]["name"]
    home = m["teams"]["home"]["name"]
    away = m["teams"]["away"]["name"]
    return f"{country} - {league} - {home} vs {away}"

print("BOT V3 DAMI - QUOTE BASSE + SEGUITE")
tg("✅ <b>BOT V3 ATTIVO</b>\n- GOL solo se CALDA/MORTA\n- Schedina1: 3 quote più basse\n- Schedina2: Over 1.5\n- Blocco Amichevoli")

while True:
    try:
        tz = pytz.timezone("Europe/Rome")
        now = datetime.now(tz)
        if now.hour==0 and now.minute<4:
            sent.clear(); last_scores.clear(); seguite.clear(); save(sent,last_scores,seguite); schedine_fatte=False

        if now.hour==10 and now.minute<4 and not schedine_fatte:
            fixtures = get_today()
            ns = [f for f in fixtures if f["fixture"]["status"]["short"]=="NS"]
            if len(ns)>=3:
                # SCHEDINA 1 - QUOTA BASSA
                quotate=[]
                for f in ns[:20]: # guarda prime 20 del giorno
                    q = get_odds_quote(f["fixture"]["id"])
                    quotate.append((q,f))
                    time.sleep(0.3)
                quotate.sort(key=lambda x: x[0])
                s1 = [x[1] for x in quotate[:3]] if quotate[0][0]!=99 else ns[:3]
                txt1="📋 <b>SCHEDINA 1 - QUOTA 1.60/1.80 - PIU' PROBABILI</b>\n\n"
                for x in s1: txt1+=f"• {format_match(x)} - {x['fixture']['date'][11:16]}\n"
                tg(txt1)
                time.sleep(1)
                # SCHEDINA 2 - OVER 1.5
                selected=[]
                for f in ns:
                    if len(selected)>=20: break
                    try:
                        if get_last5_avg(f['teams']['home']['id'])>=1.6 and get_last5_avg(f['teams']['away']['id'])>=1.6:
                            selected.append(f)
                    except: continue
                    time.sleep(0.2)
                if selected:
                    txt2=f"📊 <b>SCHEDINA 2 - OVER 1.5 - {len(selected)} PARTITE</b>\n\n"
                    for x in selected: txt2+=f"• {format_match(x)} - {x['fixture']['date'][11:16]}\n"
                    tg(txt2)
            schedine_fatte=True

        lives = get_live()
        for m in lives:
            fid=str(m["fixture"]["id"])
            minute=m["fixture"]["status"]["elapsed"] or 0
            gh=m["goals"]["home"] or 0; ga=m["goals"]["away"] or 0
            score=f"{gh}-{ga}"
            league_name=m["league"]["name"] or ""
            # BLOCCO AMICHEVOLI PRIMA DI TUTTO
            if any(x in league_name for x in ["U19","U18","U17","U16","Friendly","Friendlies","Club Friendly"]): continue

            full_name=format_match(m)
            stats=get_stats(int(fid))
            shots_on=corners=shots_tot=0
            for ts in stats:
                for s in ts.get("statistics",[]):
                    t=s.get("type",""); v=s.get("value") or 0
                    if not isinstance(v,int): continue
                    if t=="Shots on Goal": shots_on+=v
                    if "Corner" in t: corners+=v
                    if "Total Shots" in t: shots_tot+=v

            # GOL - SOLO SE ERA SEGUITA (CALDA/MORTA)
            if fid in last_scores:
                ogh,oga=last_scores[fid]
                if (gh!=ogh or ga!=oga) and fid in seguite:
                    tg(f"⚽ <b>GOL! {score} al {minute}'</b>\n{full_name}\nEra {ogh}-{oga} - Era CALDA/MORTA")
                if gh!=ogh or ga!=oga:
                    last_scores[fid]=(gh,ga); save(sent,last_scores,seguite)
            else:
                last_scores[fid]=(gh,ga)

            is_valid = (gh==0 and ga==0) or (gh==1 and ga==0) or (gh==0 and ga==1)
            if 5<minute<60 and is_valid:
                if f"tiri_{fid}" not in sent and shots_on>=6:
                    tg(f"🔥 <b>CALDA {score} al {minute}' - {shots_on} tiri</b>\n{full_name}\n📊 Tiri in porta: {shots_on}")
                    sent.add(f"tiri_{fid}"); seguite.add(fid); save(sent,last_scores,seguite)
                if f"corner_{fid}" not in sent and corners>=8:
                    tg(f"🚩 <b>CORNER {corners} al {minute}' - {score}</b>\n{full_name}\n🚩 Corner: {corners}")
                    sent.add(f"corner_{fid}"); seguite.add(fid); save(sent,last_scores,seguite)
                if f"morta_{fid}" not in sent and minute>=30 and shots_on<=3:
                    tg(f"💀 <b>MORTA {score} al {minute}' - {shots_on} tiri</b>\n{full_name}\n📊 {shots_on} tiri - {corners} corner")
                    sent.add(f"morta_{fid}"); seguite.add(fid); save(sent,last_scores,seguite)

            # ROSSO
            if f"red_{fid}" not in sent and minute<60:
                events=get_events(int(fid))
                for ev in events:
                    if ev["type"]=="Card" and "Red" in str(ev.get("detail","")):
                        rmin=ev["time"]["elapsed"] or 0
                        if 0<rmin<60:
                            tg(f"🟥 <b>ROSSO al {rmin}' (ora {minute}' {score})</b>\n{full_name}")
                            sent.add(f"red_{fid}"); save(sent,last_scores,seguite)
                            break
        time.sleep(90)
    except Exception as e:
        print(f"ERR {e}"); time.sleep(30)
