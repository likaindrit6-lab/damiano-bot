import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V3 FULL - BANDIERE + BOMBA + PROG + LIVE"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        if r.status_code == 429:
            tg("⛔️ TOKEN FINITO - pausa 1h")
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

def get_flag(paese):
    flags = {"Italy":"🇮🇹","England":"🏴󐁧󐁢󐁥󐁮󐁧󠁿","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸","Japan":"🇯🇵","Australia":"🇦🇺","Mexico":"🇲🇽","Colombia":"🇨🇴","Chile":"🇨🇱","Sweden":"🇸🇪","Norway":"🇳🇴","Denmark":"🇩🇰","Poland":"🇵🇱","Romania":"🇷🇴","Greece":"🇬🇷","Switzerland":"🇨🇭","Austria":"🇦🇹","Scotland":"🏴󐁧󐁢󐁳󐁣󐁴󠁿","World":"🌍"}
    return flags.get(paese, "🏳️")

def invia_schedine_mattina():
    try:
        oggi = datetime.now(ITALY).strftime('%Y-%m-%d')
        fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
       
