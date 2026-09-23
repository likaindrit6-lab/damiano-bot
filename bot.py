
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
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)

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
    if len(data) < 3: return 99
    tot = sum((m["goals"]["home"] or 0)+(m["goals"]["away"] or 0) for m in data)
    return tot / len(data)

print("BOT FINALE VOCALE DAMI")
tg("✅ <b>BOT FINALE VOCALE</b>\nPrima 60':\n- 6 tiri porta = CALDA\n- 8 corner = CALDA CORNER\n- 0-3 tiri porta = MORTA\nTutte 0-0 e 1-0\n+ Rosso prima 60' + GOL\n+ 2 Schedine 10:00")

while True:
    try:
        tz = pytz.timezone("Europe/Rome")
        now = datetime.now(tz)
        if now.hour == 0 and now.minute < 3:
            sent.clear(); last_scores.clear(); save(sent,last_scores); schedine_fatte=False

        # SCHEDINE 10:00
        if now.hour == 10 and now.minute < 3 and not schedine_fatte:
            fixtures = get_today()
            ns = [f for f in fixtures if f["fixture"]["status"]["short"]=="NS"]
            if len(ns)>=3:
                # Schedina 1 - quota 1.60/1.70
                s1=ns[:3]
                txt1="📋 <b>SCHEDINA 1 - QUOTA 1.60/1.70</b>\nQuota bassissima\n\n"
                for x in s1: txt1+=f"• {x['teams']['home']['name']} vs {x['teams']['away']['name']} - {x['fixture']['date'][11:16]}\n"
                tg(txt1)
                time.sleep(1)
                # Schedina 2 - quota 4.00 media 2 gol
                selected=[]
                for f in ns:
                    if len(selected)>=6: break
                    try:
                        avg = get_last5_avg(f['teams']['home']['id'])
                        if avg <= 2.3:
                            selected.append(f)
                        time.sleep(0.3)
                    except: continue
                if selected:
                    txt2=f"📊 <b>SCHEDINA 2 - QUOTA ~4.00 - {len(selected)} PARTITE DA MEDIA 2 GOL</b>\nUltime 5 partite\n\n"
                    for x in selected: txt2+=f"• {x['teams']['home']['name']} vs {x['teams']['away']['name']} - {x['fixture']['date'][11:16]}\n"
                    tg(txt2)
            schedine_fatte=True

        lives = get_live()
        for m in lives:
            fid = str(m["fixture"]["id"])
            minute = m["fixture"]["status"]["elapsed"] or 0
            gh = m["goals"]["home"] or 0
            ga = m["goals"]["away"] or 0
            home = m["teams"]["home"]["name"]; away = m["teams"]["away"]["name"]
            score = f"{gh}-{ga}"
            if "U19" in m["league"]["name"] or "U18" in m["league"]["name"] or "Friendly" in m["league"]["name"]: continue

            # STATS
            stats = get_stats(int(fid))
            shots_on=0; corners=0; shots_tot=0
            for ts in stats:
                for s in ts.get("statistics",[]):
                    t=s.get("type",""); v=s.get("value") or 0
                    if t=="Shots on Goal": shots_on+=v
                    if "Corner" in t: corners+=v
                    if "Total Shots" in t: shots_tot+=v

            # AVVISO GOL
            if fid in last_scores:
                ogh,oga = last_scores[fid]
                if gh!=ogh or ga!=oga:
                    tg(f"⚽ <b>GOL! {score} al {minute}'</b>\n{home} vs {away}\nEra {ogh}-{oga}")
                    last_scores[fid]=(gh,ga); save(sent,last_scores)

            # PRIMA DEI 60' - COME HAI DETTO TU
            if 5 < minute < 60:
                # Solo 0-0 e 1-0 / 0-1 come hai detto tu
                if not ((gh==0 and ga==0) or (gh==1 and ga==0) or (gh==0 and ga==1)):
                    pass
                else:
                    # CALDA 6 tiri in porta - SEPARATA
                    key_tiri = f"tiri_{fid}"
                    if key_tiri not in sent and shots_on >= 6:
                        tg(f"🔥 <b>CALDA TIRI {score} al {minute}'</b>\n{home} vs {away}\n📊 Tiri in porta: {shots_on}\nHa 6 tiri in porta - sta spingendo")
                        sent.add(key_tiri); save(sent,last_scores)
                        last_scores[fid]=(gh,ga)

                    # CALDA CORNER 8 corner - A PARTE come hai detto tu
                    key_corner = f"corner_{fid}"
                    if key_corner not in sent and corners >= 8:
                        tg(f"🔥 <b>CALDA CORNER {score} al {minute}'</b>\n{home} vs {away}\n🚩 Corner: {corners} al {minute}'\n8 corner prima di 60'")
                        sent.add(key_corner); save(sent,last_scores)

                    # MORTA 0-3 tiri in porta entro 60'
                    key_morta = f"morta_{fid}"
                    if key_morta not in sent and shots_on <= 3 and minute >= 30: # aspetto almeno 30'
                        tg(f"💀 <b>MORTA {score} al {minute}'</b>\n{home} vs {away}\n📊 Tiri in porta: {shots_on} - Corner: {corners}\nSolo {shots_on} tiri in porta")
                        sent.add(key_morta); save(sent,last_scores)

                # ROSSO PRIMA DEL 60'
                key_red = f"red_{fid}"
                if key_red not in sent:
                    events = get_events(int(fid))
                    for ev in events:
                        if ev["type"]=="Card" and "Red" in str(ev.get("detail","")):
                            rmin = ev["time"]["elapsed"] or 0
                            if rmin < 60:
                                tg(f"🟥 <b>ROSSO prima del 60' al {rmin}'</b>\n{home} vs {away} - {score} al {minute}'")
                                sent.add(key_red); save(sent,last_scores)
                                break

            # SOPRA 60' - come prima
            if minute >= 60:
                if fid in sent and f"over_{fid}" in sent: continue
                if not ((gh==0 and ga==0) or (gh==1 and ga==0) or (gh==0 and ga==1)): continue
                if shots_tot==0 and corners==0: continue
                key_over = f"over_{fid}"
                if key_over not in sent:
                    if shots_tot >= 8 and corners >= 6:
                        tg(f"🔥 <b>CALDA {score} al {minute}'</b>\n{home} vs {away}\n📊 Tiri:{shots_tot} ({shots_on} in porta) Corner:{corners}")
                    else:
                        tg(f"💀 <b>MORTA {score} al {minute}'</b>\n{home} vs {away}\n📊 Tiri:{shots_tot} Corner:{corners}")
                    sent.add(key_over); last_scores[fid]=(gh,ga); save(sent,last_scores)

        time.sleep(45)
    except Exception as e:
        print(f"ERR: {e}"); time.sleep(30)
