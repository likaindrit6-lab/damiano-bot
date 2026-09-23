
import os, threading, time, requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home(): 
    return "OK - Bot Live", 200

BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")

def tg(m):
 try:
  requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=10)
 except: pass

def loop():
 tg("✅ BOT RIPARTITO - fixato crash Render")
 while True:
  print("VIVO", flush=True)
  # qui poi rimettiamo la logica delle partite live
  time.sleep(90)

# Avvia il loop in background
threading.Thread(target=loop, daemon=True).start()

# QUESTA RIGA MANCAVA - tiene vivo il servizio
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
