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
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m}, timeout=20)
    except:
        pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        if r.status_code == 429:
            return "LIMIT"
        return r.json().get("response", [])
    except:
        return []

time.sleep(3)
tg("BOT ATTIVO 1T 3 TIRI 1-45 MONDO")

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
            try:
                return int(str(s['value']).replace('%','') or 0)
            except:
                return 0
    return 0

def get_sot(fid):
    d = stats_cache.get(fid)
    if d:
        return d.get('sot',0)
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
                tg("LIMIT pausa 1h")
                time.sleep(3600)
                continue
            tg(f"VIVO {len(lc)} live {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        if now.hour == 7 and now.minute < 30 and not bombe_fatte:
            fix = api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
            fix = [x for x in fix if x['fixture']['status']['short'] == 'NS']
            bombe = []
            for g in fix[:60]:
                if len(bombe)>=30:
                    break
                odds = api_get
