import os, threading, time, requests
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "OK", 200

BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")

def tg(m):
 try: requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=10)
 except: pass

def loop():
 tg("✅ BOT RIPARTITO - fixato crash Render")
 while True:
  print("VIVO", flush=True)
  time.sleep(90)

threading.Thread(target=loop, daemon=True).start()
