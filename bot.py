
import os, threading, time, requests
from flask import Flask
app = Flask(__name__)
BOT = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
KEY = os.getenv("API_FOOTBALL_KEY")

@app.route('/')
def home():
    return f"V11 OK BOT:{bool(BOT)} CHAT:{bool(CHAT)} KEY:{bool(KEY)}"

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id":CHAT,"text":t}, timeout=10)
    except: pass

def poll():
    off=0
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{BOT}/getUpdates?offset={off}&timeout=30", timeout=35).json()
            for u in r.get("result",[]):
                off=u["update_id"]+1
                if "/start" in u.get("message",{}).get("text",""):
                    send("V11 ATTIVO DAMI ✅")
        except: time.sleep(5)

threading.Thread(target=poll, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
