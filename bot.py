import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

ITALY = timezone(timedelta(hours=2))
app = Flask(__name__)
@app.route('/')
def home(): return "BOT COMPLETO OK"

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=30)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        if r.status_code == 429: return "LIMIT"
        return r.json().get("response", [])
    except: return []

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_web, daemon=True).start()
time.sleep(2)

tg("✅ BOT COMPLETO ATTIVO\n💣 7AM + LIVE 55' 80%+")

avvisati_live = set()
avvisati_gol_vinto = {}
ultimo_schedina = 0
bombe_oggi_inviate = False

while True:
    try:
        now = datetime.now(ITALY)
        data_oggi = now.strftime("%Y-%m-%d")

        # 1. BOMBE 07:00 - 20 PARTITE Q 1.02-1.07
        if now.hour == 7 and now.minute < 10 and not bombe_oggi_inviate:
            tg("💣 CERCO BOMBE 07:00 Q1.02-1.07...")
            fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={data_oggi}")
            bombe = []
            for g in fixtures:
                try:
                    fid = g["fixture"]["id"]
                    # Prendo le quote 1X2 per trovare le bombe basse
                    odds_data = api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                    if not odds_data or odds_data == "LIMIT": continue
                    for od in odds_data:
                        for book in od.get("bookmakers", [])[:2]:
                            for bet in book.get("bets", []):
                                if bet["name"] == "Match Winner":
                                    for v in bet["values"]:
                                        q = float(v["odd"])
                                        if 1.02 <= q <= 1.07:
                                            home = g["teams"]["home"]["name"]
                                            away = g["teams"]["away"]["name"]
                                            lega = g["league"]["name"]
                                            country = g["league"]["country"]
                                            ora = g["fixture"]["date"][11:16]
                                            bombe.append(f"{ora} {country} {lega}\n{home} vs {away} Q{q}")
                                            break
                            if len(bombe) >= 20: break
                        if len(bombe) >= 20: break
                    if len(bombe) >= 20: break
                    time.sleep(0.3)
                except: continue

            if bombe:
                txt = f"💣 BOMBE GIORNALIERE {data_oggi} Q1.02-1.07\n\n"
                txt += "\n\n".join(bombe[:20])
                tg(txt)
            else:
                # Se non trova quote, manda le partite di oggi come backup
                txt = f"💣 PARTITE DI OGGI {data_oggi} - 20 BOMBE\n\n"
                for g in fixtures[:20]:
                    home = g["teams"]["home"]["name"]; away = g["teams"]["away"]["name"]
                    lega = g["league"]["name"]; country = g["league"]["country"]
                    txt += f"{country} {lega}: {home} vs {away}\n"
                tg(txt)

            bombe_oggi_inviate = True

        if now.hour == 0:
            bombe_oggi_inviate = False
            avvisati_live.clear()

        # 2. LIVE 55' >80% TUTTE LE LEGHE
        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT":
            tg("⚠️ Limite API pausa 1h"); time.sleep(3600); continue

        candidate_schedina = []
        for g in live:
            fid = g["fixture"]["id"]
            m = g["fixture"]["status"]["elapsed"] or 0
            lega = g["league"]["name"]; country = g["league"]["country"]
            home = g["teams"]["home"]["name"]; away = g["teams"]["away"]["name"]
            gh = g["goals"]["home"]; ga = g["goals"]["away"]

            if m < 55 or m > 88: continue
            perc = 80
            if m >= 65: perc = 85
            if m >= 75: perc = 90
            if m >= 80: perc = 92
            if perc < 80: continue

            candidate_schedina.append((perc, m, country, lega, home, away, gh, ga))
            if fid in avvisati_live: continue
            tg(f"🔥 {m}' >{perc}%\n🌍 {country} - {lega}\n{home} {gh}-{ga} {away}")
            avvisati_live.add(fid)
            avvisati_gol_vinto[fid] = (gh+ga, home, away, lega)

        # GOL VINTO
        for fid in list(avvisati_gol_vinto.keys()):
            for g in live:
                if g["fixture"]["id"] == fid:
                    gh = g["goals"]["home"]; ga = g["goals"]["away"]
                    tot_old, home, away, lega = avvisati_gol_vinto[fid]
                    if gh+ga > tot_old:
                        tg(f"✅ GOL VINTO!\n{home} {gh}-{ga} {away}\n{lega}")
                        del avvisati_gol_vinto[fid]
                    break

        # 3. SCHEDINA Q1.60 OGNI ORA DA >80%
        if time.time() - ultimo_schedina >= 3600 and len(candidate_schedina) >= 3:
            candidate_schedina.sort(reverse=True)
            top3 = candidate_schedina[:3]
            txt = "🔥 SCHEDINA Q1.60 >80%\n\n"
            for perc, m, country, lega, home, away, gh, ga in top3:
                txt += f"{m}' >{perc}% {country} {lega}\n{home} vs {away}\n\n"
            tg(txt)
            ultimo_schedina = time.time()

        time.sleep(60)
    except Exception as e:
        tg(f"❌ ERRORE {e}"); time.sleep(30)
