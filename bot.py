import os
import time
import requests
import threading
import json
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT OK - 1T 20-45 3TIRI - 2T 70 6TIRI NO DOPPIONE"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}, timeout=20)
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

def salva_file(nome, data):
    try:
        with open(f"/tmp/{nome}.json", "w") as f:
            json.dump(data, f)
    except:
        pass

def leggi_file(nome):
    try:
        with open(f"/tmp/{nome}.json", "r") as f:
            return json.load(f)
    except:
        return None

def check_vincita(fid, tipo):
    try:
        fx = api_get(f"https://v3.football.api-sports.io/fixtures?id={fid}")
        if not fx: return None
        f = fx[0]
        if f['fixture']['status']['short'] not in ['FT', 'AET', 'PEN']: return None
        gh = f['goals']['home']; ga = f['goals']['away']
        if gh is None: return None
        t = tipo.lower()
        if "home" in t or "1 fisso" in t: return gh > ga
        if "x2" in t: return ga >= gh
        if "over 0.5" in t: return (gh + ga) >= 1
        if "over 1.5" in t: return (gh + ga) >= 2
        if "casa segna" in t: return gh >= 1
        return None
    except:
        return None

time.sleep(3)
tg("✅ BOT ATTIVO - FIX NO DOPPIONE - 1T 20-45 3TIRI / 2T 70 6TIRI")

avvisati_gol = {}
avvisati_squadra = set()
preavvisati = set()
preavvisati_1t = set()
stats_cache = {}
bombe_fatte = False
ultimo_hb = 0
ultima_schedina = 0
ultima_pre_schedina = 0

def
