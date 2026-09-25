import os, threading, time, requests
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "V21 FINAL FIX - LIVE"

port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}
BASE = "https://v3.football.api-sports.io"

print(f"TOKEN presente: {bool(TOKEN)} CHAT: {CHAT} API: {bool(API)}")

def send(t):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=20)
        print(f"SEND OK {r.status_code}")
        return True
    except Exception as e:
        print(f"SEND ERROR {e}")
        return False

# MESSAGGIO IMMEDIATO - così vedi subito nei log se manda
time.sleep(2)
send(f"✅ BOT DAMI RIPARTITO {datetime.now().astimezone().strftime('%H:%M:%S')} - SONO VIVO")

while True:
    try:
        print(f"LOOP VIVO {datetime.now().astimezone().strftime('%H:%M:%S')} - controllo...")
        # qui domani ci rimettiamo la tua logica calcio, per ora solo keep-alive per non farlo fermare
        time.sleep(60)
    except Exception as e:
        print(f"LOOP CRASH {e}")
        time.sleep(60)
