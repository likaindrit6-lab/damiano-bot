import os, time, threading, requests
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "DAMI BOT LIVE FIX"

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()

def send(t):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=20)
        print(f"SEND {r.status_code}", flush=True)
    except Exception as e:
        print(f"SEND ERR {e}", flush=True)

def bot_loop():
    print("BOT LOOP PARTITO", flush=True)
    time.sleep(2)
    send(f"✅ BOT DAMI ON - ORA GIRA DAVVERO {datetime.now().strftime('%H:%M:%S')}")
    c=0
    while True:
        try:
            c+=1
            print(f"VIVO {c} - {datetime.now().strftime('%H:%M:%S')}", flush=True)
            if c % 10 == 0:
                send(f"🔄 Ancora vivo {datetime.now().strftime('%H:%M:%S')} - non si è fermato")
            time.sleep(60)
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
            time.sleep(60)

# Faccio partire il bot in background
threading.Thread(target=bot_loop, daemon=True).start()

# Flask davanti - così Railway non lo killa
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
