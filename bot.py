import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V5 DEFINITIVO - FINE 1T + 00-10"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}, timeout=25)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=30)
        if r.status_code == 429:
            tg("TOKEN FINITO - pausa 60 min")
            return "LIMIT"
        return r.json().get("response", [])
    except: return []

def get_stat(arr, nome):
    for s in arr:
        if s.get('type') == nome:
            try:
                v = s.get('value')
                if v is None: return 0
                return int(str(v).replace('%','').strip() or 0)
            except: return 0
    return 0

def get_flag(p):
    m = {"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸","World":"🌍","Europe":"🇪🇺"}
    return m.get(p, f"[{p.upper()}]")

def invia_schedine_mattina():
    try:
        oggi = datetime.now(ITALY).strftime('%Y-%m-%d')
        fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
        if not fixtures or fixtures == "LIMIT": return
        lista = []
        for f in fixtures[:50]:
            ora = f['fixture']['date'][11:16]
            paese = f['league']['country']; lega = f['league']['name']
            flag = get_flag(paese)
            lista.append(f"{flag} {paese.upper()} - {lega} | {ora} {f['teams']['home']['name']}-{f['teams']['away']['name']}")
        if len(lista) >= 30:
            bomba = f"BOMBA 30
