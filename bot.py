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
tg("✅ BOT RIPARATO ATTIVO")

avvisati_gol = {}
avvisati_squadra = set()
preavvisati = set()
preavvisati_1t = set()
stats_cache = {}
bombe_fatte = False
ultimo_hb = 0
ultima_schedina = 0
ultima_pre_schedina = 0
ultima_schedina_30 = 0
ultima_pre_30 = 0
ultima_schedina_sicura = 0
ultima_pre_sicura = 0

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

        if time.time() - ultimo_hb > 900:
            lc = api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if lc == "LIMIT":
                tg("⚠️ LIMIT - pausa 1h"); time.sleep(3600); continue
            tg(f"✅ VIVO - {len(lc)} live - {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        if now.hour == 7 and now.minute < 30 and not bombe_fatte:
            fix = api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
            fix = [x for x in fix if x['fixture']['status']['short'] == 'NS']
            bombe = []
            for g in fix:
                if len(bombe)>=30: break
                odds = api_get(f"https://v3.football.api-sports.io/odds?fixture={g['fixture']['id']}")
                if not odds: time.sleep(0.2); continue
                for o in odds:
                    for bk in o.get("bookmakers",[])[:3]:
                        for bet in bk.get("bets",[]):
                            if bet["name"]=="Match Winner":
                                for v in bet["values"]:
                                    try:
                                        q=float(v["odd"])
                                        if 1.02 <= q <= 1.08:
                                            ora = datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY).strftime('%H:%M')
                                            bombe.append(f"{ora} {g['teams']['home']['name']} vs {g['teams']['away']['name']} Q{q}\n")
                                    except: pass
                time.sleep(0.3)
            if bombe:
                txt = f"💣 BOMBE {len(bombe)}\n\n"
                for i,b in enumerate(bombe,1): txt+=f"{i}. {b}\n"
                tg(txt)
                bombe_fatte=True

        if now.hour == 0:
            bombe_fatte=False
            avvisati_squadra.clear()
            preavvisati.clear()
            preavvisati_1t.clear()
            avvisati_gol.clear()
            stats_cache.clear()

        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT": time.sleep(3600); continue

        cand_schedina = []
        cand_schedina_50 = []
        cand_pre_schedina = []

        for g in live:
            m = g["fixture"]["status"]["elapsed"] or 0
            if m < 20 or m > 92: continue
            fid = g["fixture"]["id"]
            home = g['teams']['home']['name']
            away = g['teams']['away']['name']
            gh = g['goals']['home']
            ga = g['goals']['away']
            country = g['league']['country']

            sot_tot = get_sot(fid)
            if fid not in stats_cache:
                try:
                    st = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if st and len(st)>=2:
                        hs = st[0]['statistics']
                        aws = st[1]['statistics']
                        sot = get_stat(hs,'Shots on Goal') + get_stat(aws,'Shots on Goal')
                        tot = get_stat(hs,'Total Shots') + get_stat(aws,'Total Shots')
                        dang = get_stat(hs,'Dangerous Attacks') + get_stat(aws,'Dangerous Attacks')
                        perc = 0
                        if sot >= 5 and dang >= 35: perc = 92
                        elif sot >= 4 and dang >= 28: perc = 89
                        elif sot >= 3 and dang >= 25 and tot >= 7: perc = 86
                        stats_cache[fid] = {'perc': perc, 'sot': sot, 'time': time.time()}
                        sot_tot = sot
                        time.sleep(0.3)
                except: pass

            if 20 <= m <= 45 and fid not in preavvisati_1t:
                if get_sot(fid) >= 3:
                    d = stats_cache.get(fid,{})
                    if d.get('perc',0) >= 85:
                        tg(f"⚽️ 1T >{d['perc']}% {m}' {home} {gh}-{ga} {away} TiriP:{d['sot']}")
                        preavvisati_1t.add(fid)

            if m >= 60 and sot_tot < 5:
                continue

            if 70 <= m <= 85:
                cand_schedina.append(g)
                cand_schedina_50.append(g)

            if 60 <= m <= 69:
                cand_pre_schedina.append(g)

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
                m=g["fixture"]["status"]["elapsed"]
                fid=g["fixture"]["id"]
                txt+=f"{m}' TiriP:{get_sot(fid)} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n\n"
            tg(txt); ultima_pre_schedina=time.time()

        if time.time() - ultima_schedina > 3600 and len(cand_schedina)>=3:
            txt=f"🔥 SCHEDINA 70' >90% {now.strftime('%H:%M')}\n\n"
            for g in cand_schedina[:4]:
                m=g["fixture"]["status"]["elapsed"]
                fid=g["fixture"]["id"]
                txt+=f"{m}' TiriP:{get_sot(fid)} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n\n"
            tg(txt); ultima_schedina=time.time()

        if time.time() - ultima_pre_30 > 1200 and len(cand_schedina_50)>=3 and time.time() - ultima_schedina_30 > 1200:
            tg(f"👀 PREPARATI 4 PARTITE tra 10 min {now.strftime('%H:%M')}")
            ultima_pre_30=time.time()

        if time.time() - ultima_schedina_30 > 1800 and len(cand_schedina_50)>=4:
            txt=f"📋 SCHEDINA 4 PARTITE 70' {now.strftime('%H:%M')}\n\n"
            for g in cand_schedina_50[:4]:
                m=g["fixture"]["status"]["elapsed"]
                fid=g["fixture"]["id"]
                txt+=f"{m}' TiriP:{get_sot(fid)} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n\n"
            tg(txt); ultima_schedina_30=time.time()

        time.sleep(60)
    except Exception as e:
        print(f"ERR {e}", flush=True); time.sleep(30)
