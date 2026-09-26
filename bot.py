import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

ITALY = timezone(timedelta(hours=2)) # CEST Italia
app = Flask(__name__)
@app.route('/')
def home(): return "BOT ON - " + datetime.now(ITALY).strftime('%H:%M:%S')

def tg(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        j = r.json()
        if r.status_code == 429: return "LIMIT"
        return j.get("response", [])
    except: return []

# resto del codice uguale a quello che ti ho mandato, solo cambia datetime.now(ITALY)
