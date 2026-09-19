
import os
import time
import requests
from flask import Flask
import threading

# Prende i nomi che hai tu su Render
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY") or os.getenv("API_KEY")

def manda_telegram(messaggio):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": messaggio})

def avvia_bot():
    # Questo è il messaggio di prova che volevi
    manda_telegram("Bot Damiano partito e online! ✅\nControllo partite ogni minuto.")
    print("Messaggio di avvio inviato")
    
    while True:
        try:
            print(f"Controllo fatto {time.strftime('%H:%M:%S')}")
            # qui c'è il tuo controllo partite
            # per ora lasciamo il log che hai già
            headers = {"x-apisports-key": API_KEY}
            # esempio chiamata, se non trova partite stampa 0
            # puoi tenere la tua logica qui sotto
            time.sleep(60)
        except Exception as e:
            print(f"Errore: {e}")
            time.sleep(60)

# Flask per tenere acceso Render
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Damiano online"

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
