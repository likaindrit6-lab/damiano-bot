import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT FINALE 1T+70 OK"
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
tg("✅ BOT FINALE RIPARATO ATTIVO\n⚽️ 20'-45' PRIMO TEMPO >85%\n👀 60' PREPARATI (50 min)\n🔥 70' GIOCALO >90% (60 min)")

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

        # PREAVVISO 10 MIN PRIMA SCHEDINA SICURA - OGNI 2 ORE
        if time.time() - ultima_schedina_sicura > 6600 and time.time() - ultima_pre_sicura > 6600:
            tg(f"👀 PREPARATI tra 10 min - SCHEDINA 10 SICURE 1X+Over 0.5\n⏰ {now.strftime('%H:%M')} sta arrivando...")
            ultima_pre_sicura = time.time()

        if time.time() - ultima_schedina_sicura > 7200:
            try:
                fix = api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
                fix = [x for x in fix if
