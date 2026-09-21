
import os, time, threading, requests
from flask import Flask

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
app = Flask(__name__)

@app.route('/')
def home():
    return f"V9 LIVE - API {API_KEY[:5] if API_KEY else 'NO'} - BOT OK"

def tg_loop():
    offset=0
    while True:
        try:
            url=f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=20"
            data=requests.get(url, timeout=25).json()
            for upd in data.get("result",[]):
                offset=upd["update_id"]+1
                chat=upd.get("message",{}).get("chat",{}).get("id")
                txt=upd.get("message",{}).get("text","")
                if chat and "/start" in txt:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id":chat,"text":"✅ DAMI SONO LIVE V9! Verde fisso. Ora ti carico il sistema 90sec con 10 partite."}, timeout=10)
        except Exception as e:
            print(e)
            time.sleep(5)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    tg_loop()
