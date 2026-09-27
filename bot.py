import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT FINALE 1T+60-70 OK"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode":"HTML"}, timeout=20)
    except Exception as e: print(f"TG ERR {e}", flush=True)

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        print(f"API {r.status_code} {url[-50:]}", flush=True)
        if r.status_code == 429: return "LIMIT"
        return r.json().get("response", [])
    except Exception as e:
        print(f"API ERR {e}", flush=True); return []

time.sleep(3)
tg("✅ BOT FINALE ATTIVO\n⚽️ 20'-45' PRIMO TEMPO >85%\n👀 60' PREPARATI\n🔥 70' GIOCALO >90%")

avvisati_gol = {}
avvisati_squadra = set()
preavvisati = set()
preavvisati_1t = set() # primo tempo
stats_cache = {}
bombe_fatte = False
ultimo_hb = 0
ultima_schedina = 0

def get_stat(arr, nome):
    for s in arr:
        if s['type'] == nome:
            try: return int(str(s['value']).replace('%','') or 0)
            except: return 0
    return 0

while True:
    try:
        now = datetime.now(ITALY)

        if time.time() - ultimo_hb > 900:
            lc = api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if lc == "LIMIT":
                tg("⚠️ LIMIT API - pausa 1h"); time.sleep(3600); continue
            tg(f"✅ BOT VIVO - {len(lc)} live - {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        if now.hour == 7 and now.minute < 30 and not bombe_fatte:
            tg(f"💣 BOMBE {now.strftime('%Y-%m-%d')} CERCO 30...")
            fix = api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
            fix = [x for x in fix if x['fixture']['status']['short'] == 'NS']
            bombe = []
            for g in fix:
                try:
                    if len(bombe)>=30: break
                    odds = api_get(f"https://v3.football.api-sports.io/odds?fixture={g['fixture']['id']}")
                    if odds == "LIMIT": time.sleep(2); continue
                    if not odds: time.sleep(0.2); continue
                    for o in odds:
                        for bk in o.get("bookmakers",[])[:5]:
                            for bet in bk.get("bets",[]):
                                if bet["name"]=="Match Winner":
                                    for v in bet["values"]:
                                        try:
                                            q=float(v["odd"])
                                            if 1.02 <= q <= 1.08:
                                                ora = datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY).strftime('%H:%M')
                                                bombe.append(f"{ora} - {g['league']['country']} {g['league']['name']}\n{g['teams']['home']['name']} vs {g['teams']['away']['name']} => {v['value']} Q{q}\n")
                                                raise StopIteration
                                        except: continue
                    time.sleep(0.3)
                except StopIteration: continue
                except: continue
            if bombe:
                testo = f"💣 BOMBE TROVATE {len(bombe)}\n\n"
                for i, b in enumerate(bombe, 1):
                    testo += f"{i}. {b}\n"
                    if i % 10 == 0: tg(testo); testo = ""; time.sleep(1)
                if testo: tg(testo)
                if len(bombe) >= 15: bombe_fatte = True

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
        for g in live:
            m = g["fixture"]["status"]["elapsed"] or 0
            if m < 20 or m > 92: continue
            fid = g["fixture"]["id"]
            home = g['teams']['home']['name']
            away = g['teams']['away']['name']
            gh = g['goals']['home']
            ga = g['goals']['away']
            country = g['league']['country']
            lega = g['league']['name']

            # --- 20'-45' PRIMO TEMPO >85% ---
            if 20 <= m <= 45 and fid not in preavvisati_1t:
                # cache stats ogni 3 min per non bruciare API
                if fid not in stats_cache or time.time() - stats_cache[fid]['time'] > 180:
                    st = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if st!= "LIMIT" and st and len(st)>=2:
                        try:
                            hs = st[0]['statistics']
                            aws = st[1]['statistics']
                            sot = get_stat(hs,'Shots on Goal') + get_stat(aws,'Shots on Goal')
                            tot_s = get_stat(hs,'Total Shots') + get_stat(aws,'Total Shots')
                            dang = get_stat(hs,'Dangerous Attacks') + get_stat(aws,'Dangerous Attacks')
                            corn = get_stat(hs,'Corner Kicks') + get_stat(aws,'Corner Kicks')

                            perc1 = 0
                            if sot >= 5 and dang >= 35: perc1 = 92
                            elif sot >= 4 and dang >= 28: perc1 = 89
                            elif sot >= 3 and dang >= 25 and tot_s >= 7: perc1 = 86

                            stats_cache[fid] = {'perc': perc1, 'time': time.time(), 'sot': sot, 'dang': dang, 'corn': corn, 'tot': tot_s}
                            time.sleep(0.4)
                        except: pass

                if fid in stats_cache and stats_cache[fid]['perc'] >= 85:
                    d = stats_cache[fid]
                    tg(f"⚽️ PRIMO TEMPO >{d['perc']}%\n⏱️ {m}' {home} {gh}-{ga} {away}\n🌍 {country} {lega}\n📊 TiriP:{d['sot']} Tot:{d['tot']} Pericolosi:{d['dang']} Angoli:{d['corn']}\n🔥 GOL 1° TEMPO!")
                    preavvisati_1t.add(fid)

            # --- 60' + 70' SECONDO TEMPO ---
            if m < 60: continue
            perc = min(96, 70 + (m-45)) # 60'=85%, 70'=95%

            if 70 <= m <= 92:
                cand_schedina.append(g)

            if 60 <= m <= 69 and fid not in preavvisati:
                tg(f"👀 PREPARATI {m}' >{perc}%\n{home} {gh}-{ga} {away}\n🌍 {country} {lega}\n⏳ Al 70' si gioca!")
                preavvisati.add(fid)

            if 70 <= m <= 92 and fid not in avvisati_squadra:
                squadra = home if gh <= ga else away
                tg(f"🔥 GIOCALO ORA {m}' >{perc}%\n{home} {gh}-{ga} {away}\n🌍 {country} {lega}\n⚽️ NEXT GOAL {squadra} >{perc}%")
                avvisati_squadra.add(fid)
                avvisati_gol[fid] = gh+ga

        for g in live:
            fid=g["fixture"]["id"]
            if fid in avvisati_gol:
                tot=g["goals"]["home"]+g["goals"]["away"]
                if tot > avvisati_gol[fid]:
                    tg(f"✅ GOL VINTO >90%!\n{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n{g['league']['name']}")
                    del avvisati_gol[fid]

        if time.time() - ultima_schedina > 3600 and len(cand_schedina)>=3:
            txt="🔥 SCHEDINA Q1.60 >90%\n\n"
            for g in cand_schedina[:3]:
                m=g["fixture"]["status"]["elapsed"]
                txt+=f"{m}' {g['league']['country']} {g['teams']['home']['name']} vs {g['teams']['away']['name']}\n\n"
            tg(txt); ultima_schedina=time.time()

        time.sleep(60)
    except Exception as e:
        print(f"LOOP ERR {e}", flush=True); time.sleep(30)
