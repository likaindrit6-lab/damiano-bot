import os, threading, time, requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "TEST OK"

port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()

def send(t):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=15)
        print("SEND:", r.status_code, r.text[:200])
    except Exception as e:
        print("ERR", e)

time.sleep(3)
send(f"✅ TEST BOT DAMI OK - {datetime.now().astimezone().strftime('%H:%M:%S')} - se leggi questo gira!")

# loop vuoto per tenere vivo
while True:
    print("vivo", datetime.now().astimezone().strftime("%H:%M:%S"))
    time.sleep(60)
