
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
                return set(d.get("sent",[])), d.get("scores",{})
    except: pass
    return set(), {}
def save(sent_set, scores_dict):
    try:
        with open(FILE,"w") as f: json.dump({"sent": list(sent_set), "scores": scores_dict}, f)
    except: pass

sent, last_scores = load()
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

def format_match(m):
    # QUI AGGIUNTO PAESE + SERIE
    country = m["league"]["country"] or ""
    league = m["league"]["name"] or ""
    home = m["teams"]["home"]["name"]
    away = m["teams"]["away"]["name"]
    return f"{country} - {league} - {home} vs {away}"

print("BOT FINALE VOCALE DAMI V2 - 4 ALERT + PAESE")
tg("✅ <b>BOT V2 ATTIVO</b>\nOgni 90 sec:\n🔥 CALDA 6 tiri <60'\n🚩 CALDA 8 corner <60'\n💀 MORTA 0-3 tiri <60'\n🟥 ROSSO <60'\nTutte con Paese+Serie\n+ 2 Schedine 10:00")

while True:
    try:
        tz = pytz.timezone("Europe/Rome")
        now = datetime.now(tz)
        if now.hour == 0 and now.minute < 4:
            sent.clear(); last_scores.clear(); save(sent,last_scores); schedine_fatte=False

        # SCHEDINE 10:00 - COME HAI DETTO TU LE LASCIO
        if now.hour == 10 and now.minute < 4 and not schedine_fatte:
            fixtures = get_today()
            ns = [f for f in fixtures if f["fixture"]["status"]["short"]=="NS"]
            if len(ns)>=3:
                # Schedina 1 - QUOTA 1.70/1.80 FACILI - LA LASCIO
                s1=ns[:3]
                txt1="📋 <b>SCHEDINA 1 - QUOTA 1.70/1.80</b>\nPartite facili\n\n"
                for x in s1:
                    txt1+=f"• {format_match(x)} - {x['fixture']['date'][11:16]}\n"
                tg(txt1)
                time.sleep(1)
                # Schedina 2 - NUOVA LOGICA: SOLO OVER 1.5 ULTIME 5
                selected=[]
                for f in ns:
                    if len(selected)>=20: break # max 20 per non spammare
                    try:
                        avg_home = get_last5_avg(f['teams']['home']['id'])
                        avg_away = get_last5_avg(f['teams']['away']['id'])
                        # Se entrambe le squadre nelle ultime 5 hanno media > 1.5 gol a partita = Over 1.5
                        if avg_home >= 1.6 and avg_away >= 1.6:
                            selected.append(f)
                        time.sleep(0.25)
                    except: continue
                if selected:
                    txt2=f"📊 <b>SCHEDINA 2 - LISTA OVER 1.5 (ultime 5)</b>\n{len(selected)} partite filtrate oggi\n\n"
                    for x in selected:
                        txt2+=f"• {format_match(x)} - {x['fixture']['date'][11:16]}\n"
                    tg(txt2)
                else:
                    tg("📊 Schedina 2: oggi nessuna partita con media Over 1.5 nelle ultime 5")
            schedine_fatte=True

        lives = get_live()
        for m in lives:
            fid = str(m["fixture"]["id"])
            minute = m["fixture"]["status"]["elapsed"] or 0
            gh = m["goals"]["home"] or 0
            ga = m["goals"]["away"] or 0
            score = f"{gh}-{ga}"
            full_name = format_match(m)

            if "U19" in m["league"]["name"] or "U18" in m["league"]["name"] or "Friendly" in m["league"]["name"]: continue

            # STATS
            stats = get_stats(int(fid))
            shots_on=0; corners=0; shots_tot=0
            for ts in stats:
                for s in ts.get("statistics",[]):
                    t=s.get("type",""); v=s.get("value") or 0
                    if t=="Shots on Goal": shots_on+=v if isinstance(v,int) else 0
                    if "Corner" in t: corners+=v if isinstance(v,int) else 0
                    if "Total Shots" in t: shots_tot+=v if isinstance(v,int) else 0

            # GOL
            if fid in last_scores:
                ogh,oga = last_scores[fid]
                if gh!=ogh or ga!=oga:
                    tg(f"⚽ <b>GOL! {score} al {minute}'</b>\n{full_name}\nEra {ogh}-{oga}")
                    last_scores[fid]=(gh,ga); save(sent,last_scores)
            else:
                last_scores[fid]=(gh,ga)

            # FILTRO 0-0 e 1-0 / 0-1 COME HAI DETTO
            is_valid_score = (gh==0 and ga==0) or (gh==1 and ga==0) or (gh==0 and ga==1)

            if 5 < minute < 60 and is_valid_score:
                # 1. CALDA TIRI - SEPARATA
                key_tiri = f"tiri_{fid}"
                if key_tiri not in sent and shots_on >= 6:
                    tg(f"🔥 <b>CALDA {score} al {minute}' - {shots_on} tiri porta</b>\n{full_name}\n📊 Tiri in porta: {shots_on}")
                    sent.add(key_tiri); save(sent,last_scores)

                # 2. CORNER - A PARTE COME HAI DETTO
                key_corner = f"corner_{fid}"
                if key_corner not in sent and corners >= 8:
                    tg(f"🚩 <b>CORNER {corners} al {minute}' - {score}</b>\n{full_name}\n🚩 Corner: {corners} al {minute}'")
                    sent.add(key_corner); save(sent,last_scores)

                # 3. MORTA max 3 tiri - AL ROVESCIO
                key_morta = f"morta_{fid}"
                if key_morta not in sent and minute >= 30 and shots_on <= 3:
                    tg(f"💀 <b>MORTA {score} al {minute}' - {shots_on} tiri</b>\n{full_name}\n📊 Tiri: {shots_on} - Corner: {corners}")
                    sent.add(key_morta); save(sent,last_scores)

            # 4. ROSSO ENTRO 60' - SEPARATO
            key_red = f"red_{fid}"
            if key_red not in sent and minute < 60:
                events = get_events(int(fid))
                for ev in events:
                    if ev["type"]=="Card" and "Red" in str(ev.get("detail","")):
                        rmin = ev["time"]["elapsed"] or 0
                        if rmin < 60 and rmin > 0:
                            tg(f"🟥 <b>ROSSO al {rmin}' (ora {minute}' - {score})</b>\n{full_name}")
                            sent.add(key_red); save(sent,last_scores)
                            break

        time.sleep(90) # COME HAI DETTO OGNI 90 SEC
    except Exception as e:
        print(f"ERR: {e}"); time.sleep(30)
