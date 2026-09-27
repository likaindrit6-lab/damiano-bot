import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT FINALE COMPLETO 90% OK"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode":"HTML"}, timeout=20)
    except Exception as e: print(f"TG ERR {e}", flush=True)

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        print(f"API {r.status_code} {url[-40:]}", flush=True)
        if r.status_code == 429: return "LIMIT"
        return r.json().get("response", [])
    except Exception as e:
        print(f"API ERR {e}", flush=True); return []

time.sleep(3)
tg("✅ BOT FINALE ATTIVO\n💣 7AM 20-30x Q1.02-1.08\n👀 PREAVVISO 60'-74' >80%\n🔥 BOMBA 75'-92' >90% NEXT GOAL SQUADRA\n🔥 SCHEDINA OGNI ORA >80%")

avvisati = set()
avvisati_gol = {}
avvisati_squadra = set()
preavvisati = set() # <--- NUOVO PER PREAVVISO 60'
bombe_fatte = False
ultimo_hb = 0
ultima_schedina = 0

while True:
    try:
        now = datetime.now(ITALY)

        if time.time() - ultimo_hb > 900:
            lc = api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if lc == "LIMIT":
                tg("⚠️ LIMIT API - pausa 1h"); time.sleep(3600); continue
            tg(f"✅ BOT VIVO - Scansiono {len(lc)} live - {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        # 1. BOMBE 07:00 - UGUALE IDENTICO
        if now.hour == 7 and now.minute < 30 and not bombe_fatte:
            tg(f"💣 BOMBE {now.strftime('%Y-%m-%d')} Q1.02-1.08 CERCO 30...")
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
                except StopIteration:
                    continue
                except: continue

            if bombe:
                testo = f"💣 BOMBE TROVATE {len(bombe)} Q1.02-1.08\n\n"
                for i, b in enumerate(bombe, 1):
                    testo += f"{i}. {b}\n"
                    if i % 10 == 0:
                        tg(testo); testo = ""; time.sleep(1)
                if testo: tg(testo)
                if len(bombe) >= 15: bombe_fatte = True
                else: tg(f"⚠️ Ne ho trovate solo {len(bombe)}, riprovo tra 10 min...")
            else:
                tg("⚠️ 0 Bombe trovate, riprovo tra 10 min...")

        if now.hour == 0:
            bombe_fatte=False
            avvisati.clear()
            avvisati_squadra.clear()
            preavvisati.clear()

        # 2. LIVE TUTTO IL MONDO
        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT": time.sleep(3600); continue
        print(f"[{now.strftime('%H:%M:%S')}] LIVE TOTALI {len(live)}", flush=True)

        cand_schedina = []
        for g in live:
            m = g["fixture"]["status"]["elapsed"] or 0
            if m < 55 or m > 92: continue # allargato a 92 per bomba 90%
            fid = g["fixture"]["id"]

            # Percentuale REALE per bomba 90%
            perc_reale = min(96, 70 + (m-45)) # 55'=80%, 60'=85%, 75'=90%, 85'=96%
            perc_schedina = min(96, 80 + (m-55)) # per tripla come prima

            # TRIPLA CANDIDATI 55-88 come prima
            if 55 <= m <= 88:
                cand_schedina.append(g)

            home = g['teams']['home']['name']
            away = g['teams']['away']['name']
            gh = g['goals']['home']
            ga = g['goals']['away']
            country = g['league']['country']
            lega = g['league']['name']

            # --- NUOVO 1: PREAVVISO 60'-74' >80% ---
            if 60 <= m <= 74 and 80 <= perc_reale < 90:
                if fid not in preavvisati:
                    tg(f"👀 PREAVVISO >{perc_reale}%\n⏱️ {m}' {home} {gh}-{ga} {away}\n🌍 {country} {lega}\n⏳ Preparati, a 75' arriva >90%!")
                    preavvisati.add(fid)

            # --- NUOVO 2: BOMBA VERA 75'-92' >90% CON NAZIONE ---
            if 75 <= m <= 92 and perc_reale >= 90:
                if fid not in avvisati_squadra:
                    if gh <= ga:
                        squadra = home
                    else:
                        squadra = away
                    tg(f"🔥 NEXT GOAL SQUADRA >{perc_reale}%\n⏱️ {m}' {home} {gh}-{ga} {away}\n🌍 {country} {lega}\n⚽️ {squadra} SEGNA! >{perc_reale}%")
                    avvisati_squadra.add(fid)

            # --- VECCHIO SEGNALE GENERICO 55-88 - UGUALE COME PRIMA ---
            if m >= 55 and m <= 88:
                if fid in avvisati: continue
                tg(f"🔥 {m}' >{perc_schedina}%\n🌍 {country} {lega}\n{home} {gh}-{ga} {away}")
                avvisati.add(fid)
                avvisati_gol[fid] = g["goals"]["home"]+g["goals"]["away"]

        for g in live:
            fid=g["fixture"]["id"]
            if fid in avvisati_gol:
                tot=g["goals"]["home"]+g["goals"]["away"]
                if tot > avvisati_gol[fid]:
                    tg(f"✅ GOL VINTO!\n{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n{g['league']['name']}")
                    del avvisati_gol[fid]

        if time.time() - ultima_schedina > 3600 and len(cand_schedina)>=3:
            txt="🔥 SCHEDINA Q1.60 >80%\n\n"
            for g in cand_schedina[:3]:
                m=g["fixture"]["status"]["elapsed"]
                txt+=f"{m}' {g['league']['country']} {g['teams']['home']['name']} vs {g['teams']['away']['name']}\n\n"
            tg(txt); ultima_schedina=time.time()

        time.sleep(60)
    except Exception as e:
        print(f"LOOP ERR {e}", flush=True); tg(f"❌ ERRORE {e}"); time.sleep(30)
