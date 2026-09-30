import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT OK"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode":"HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        if r.status_code == 429: return "LIMIT"
        return r.json().get("response", [])
    except: return []

time.sleep(3)
tg("✅ BOT RIPARATO ATTIVO - 1T a 2 TIRI")

avvisati_gol = {}
avvisati_squadra = set()
preavvisati = set()
preavvisati_1t = set()
stats_cache = {}
bombe_fatte = False
ultimo_hb = 0
ultima_schedina = 0
ultima_pre_schedina = 0

def get_stat(arr, nome):
    for s in arr:
        if s['type'] == nome:
            try: return int(str(s['value']).replace('%','') or 0)
            except: return 0
    return 0

def get_sot(fid):
    d = stats_cache.get(fid)
    if d: return d.get('sot',0)
    return 0

while True:
    try:
        now = datetime.now(ITALY)

        if 0 <= now.hour < 7:
            if now.hour == 0:
                bombe_fatte=False
                avvisati_squadra.clear()
                preavvisati.clear()
                preavvisati_1t.clear()
                avvisati_gol.clear()
                stats_cache.clear()
            time.sleep(1800)
            continue

        if time.time() - ultimo_hb > 3600:
            lc = api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if lc == "LIMIT":
                tg("⚠️ LIMIT - pausa 1h"); time.sleep(3600); continue
            tg(f"✅ VIVO - {len(lc)} live - {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        if now.hour == 7 and now.minute < 30 and not bombe_fatte:
            fix = api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
            fix = [x for x in fix if x['fixture']['status']['short'] == 'NS']
            bombe = []
            for g in fix[:60]:
                if len(bombe)>=30: break
                odds = api_get(f"https://v3.football.api-sports.io/odds?fixture={g['fixture']['id']}")
                if not odds: time.sleep(0.2); continue
                for o in odds:
                    for bk in o.get("bookmakers",[])[:2]:
                        for bet in bk.get("bets",[]):
                            if bet["name"]=="Match Winner":
                                for v in bet["values"]:
                                    try:
                                        q=float(v["odd"])
                                        if 1.02 <= q <= 1.08:
                                            ora = datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY).strftime('%H:%M')
                                            bombe.append(f"{ora} {g['teams']['home']['name']} vs {g['teams']['away']['name']} Q{q}\n")
                                    except: pass
                time.sleep(0.4)
            if bombe:
                txt = f"💣 BOMBE {len(bombe)} - {now.strftime('%d/%m %H:%M')}\n\n"
                for i,b in enumerate(bombe,1): txt+=f"{i}. {b}\n"
                tg(txt)
            bombe_fatte=True

        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT": time.sleep(3600); continue
        if len(live) == 0:
            time.sleep(180)
            continue

        TTL_STATS = 120 if len(live) >= 4 else 300
        SLEEP_LOOP = 60 if len(live) >= 4 else 75

        cand_schedina = []
        cand_pre_schedina = []

        for g in live:
            m = g["fixture"]["status"]["elapsed"] or 0
            if m < 20 or m > 92: continue
            fid = g["fixture"]["id"]
            home = g['teams']['home']['name']
            away = g['teams']['away']['name']
            gh = g['goals']['home']
            ga = g['goals']['away']

            d = stats_cache.get(fid)
            if not d or time.time() - d.get('time',0) > TTL_STATS:
                try:
                    st = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if st and len(st)>=2:
                        hs = st[0]['statistics']
                        aws = st[1]['statistics']
                        sot = get_stat(hs,'Shots on Goal') + get_stat(aws,'Shots on Goal')
                        tot = get_stat(hs,'Total Shots') + get_stat(aws,'Total Shots')
                        dang = get_stat(hs,'Dangerous Attacks') + get_stat(aws,'Dangerous Attacks')
                        perc = 0
                        if sot >= 4 and dang >= 25: perc = 92
                        elif sot >= 3 and dang >= 20: perc = 88
                        elif sot >= 2 and dang >= 15: perc = 82
                        elif sot >= 2 and dang >= 10: perc = 75
                        stats_cache[fid] = {'perc': perc, 'sot': sot, 'time': time.time()}
                        time.sleep(0.4)
                except: pass

            sot_tot = get_sot(fid)
            # 1T ABBASSATO A 2 TIRI
            if 20 <= m <= 45 and fid not in preavvisati_1t:
                d = stats_cache.get(fid,{})
                if d.get('perc',0) >= 75 and d.get('sot',0) >= 2:
                    tg(f"⚽️ 1T >{d['perc']}% {m}' {home} {gh}-{ga} {away} TiriP:{d['sot']}")
                    preavvisati_1t.add(fid)

            if m >= 60 and sot_tot < 5: continue
            if 70 <= m <= 85: cand_schedina.append(g)
            if 60 <= m <= 69: cand_pre_schedina.append(g)
            if m < 60: continue
            perc = min(96, 70 + (m-45))
            if 60 <= m <= 69 and fid not in preavvisati:
                tg(f"👀 PREPARATI {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away}")
                preavvisati.add(fid)
            if 70 <= m <= 92 and fid not in avvisati_squadra:
                squadra = home if gh <= ga else away
                tg(f"🔥 GIOCALO {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away} NEXT {squadra}")
                avvisati_squadra.add(fid)
                avvisati_gol[fid] = gh+ga

        for g in live:
            fid=g["fixture"]["id"]
            if fid in avvisati_gol:
                tot=g["goals"]["home"]+g["goals"]["away"]
                if tot > avvisati_gol[fid]:
                    tg(f"✅ GOL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                    del avvisati_gol[fid]

        if time.time() - ultima_pre_schedina > 3000 and len(cand_pre_schedina)>=3:
            txt=f"👀 PREPARATI 10 MIN - 70'! {now.strftime('%H:%M')}\n\n"
            for g in cand_pre_schedina[:4]:
                txt+=f"{g['fixture']['status']['elapsed']}' TiriP:{get_sot(g['fixture']['id'])} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n\n"
            tg(txt); ultima_pre_schedina=time.time()

        if time.time() - ultima_schedina > 3600 and len(cand_schedina)>=3:
            txt=f"🔥 SCHEDINA 70' >90% {now.strftime('%H:%M')}\n\n"
            for g in cand_schedina[:4]:
                txt+=f"{g['fixture']['status']['elapsed']}' TiriP:{get_sot(g['fixture']['id'])} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n\n"
            tg(txt); ultima_schedina=time.time()

        time.sleep(SLEEP_LOOP)
    except Exception as e:
        print(f"ERR {e}", flush=True); time.sleep(30)
