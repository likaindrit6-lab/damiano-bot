import os, requests, threading
from flask import Flask

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")

app=Flask(__name__)
@app.route('/')
def home(): return "BOT MINIMO OK",200
@app.route('/health')
def health(): return "OK",200

def tg(m):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": m}, timeout=10)
    except: pass

def poll():
    last=0
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last+1}&timeout=20", timeout=30).json()
            if r.get("ok"):
                for u in r["result"]:
                    last=u["update_id"]
                    txt=u.get("message",{}).get("text","").lower()
                    if "accendi" in txt or "/start" in txt:
                        tg("BOT MINIMO ATTIVO - VERDE! Ora posso rimettere schedina oraria")
        except: pass

threading.Thread(target=poll, daemon=True).start()

if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
