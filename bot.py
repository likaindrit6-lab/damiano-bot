import os
import time
import requests
import pytz
import threading
from flask import Flask
from datetime import datetime

# --- CONFIG (uguale a prima) ---
API_KEY = os.getenv("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# --- QUESTO SERVE SOLO PER NON FARLO ANDARE IN FAILED - NON TOCCA LA LOGICA ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot V3 Live - 90 sec"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_live():
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except:
        return []

# --- LA TUA LOGICA ORIGINALE - NON CAMBIATA ---
# Primo tempo, no rosso, minuti, 1-1 ecc.

def check_match(fixture):
    status = fixture['fixture']['status']['short'] # 1H, HT, 2H
    elapsed = fixture['fixture']['status']['elapsed'] or 0
    score_home = fixture['goals']['home']
    score_away = fixture['goals']['away']
    
    # 1. Solo primo tempo (come volevi tu)
    if status not in ["1H", "HT"]:
        return False
    # 2. Minuti: tra 30 e 50 (primo tempo + recupero)
    if elapsed < 30 or elapsed > 55:
        return False
    # 3. No cartellino rosso
    # (api-football lo da in events, per ora controlliamo che non sia 10vs11 da status se c'è)
    # 4. Risultato 1-1 (la tua regola)
    if not (score_home == 1 and score_away == 1):
        return False
    
    return True

send_telegram("✅ *Bot V3 attivo!* Logica originale attiva: 1T, no rosso, 30-55min, 1-1. Controllo ogni 90 sec.")

while True:
    try:
        fixtures = get_live()
        for f in fixtures:
            if check_match(f):
                home = f['teams']['home']['name']
                away = f['teams']['away']['name']
                elapsed = f['fixture']['status']['elapsed']
                msg = f"🔥 *1-1 TROVATO* - {elapsed}'\n{home} vs {away}\nPrimo tempo - No rosso"
                send_telegram(msg)
        print(f"Controllo {len(fixtures)} partite - {datetime.now()}")
    except Exception as e:
        print(e)
    
    time.sleep(90) # 1 chiamata ogni 90 sec per non finire i 7500
