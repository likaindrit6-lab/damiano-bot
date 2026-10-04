import os
import time
import requests
from flask import Flask

# --- CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN") # su Render hai già messo il token
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# Variabile per la pausa - questa è la novità V9
IS_PAUSED = False

@app.route('/')
def home():
    status = "IN PAUSA ⏸️" if IS_PAUSED else "ATTIVO ✅"
    return f"Bot Damiano V9 - {status} - Live"

def send_message(chat_id, text):
    try:
        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
    except:
        pass

def handle_commands(chat_id, text):
    global IS_PAUSED
    text = text.lower().strip()

    if text == "/pausa":
        IS_PAUSED = True
        send_message(chat_id, "⏸️ Bot in PAUSA. Non consumo più richieste.\nScrivi /riprendi per riattivarmi.")
        return True
    
    if text == "/riprendi":
        IS_PAUSED = False
        send_message(chat_id, "✅ Bot RIPRESO! Sono di nuovo attivo.")
        return True
    
    return False

def run_bot():
    global IS_PAUSED
    print("Bot V9 Avviato...")
    offset = 0
    while True:
        # SE IN PAUSA: non chiamiamo Telegram = 0 richieste consumate
        if IS_PAUSED:
            print("Bot in pausa... dormo 30 sec (0 richieste)")
            time.sleep(30)
            continue

        try:
            resp = requests.get(f"{API_URL}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=30).json()
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if not chat_id or not text:
                    continue

                # Controlla se è un comando pausa/riprendi
                if handle_commands(chat_id, text):
                    continue

                # QUI METTI LA TUA LOGICA NORMALE DEL BOT
                # Esempio:
                send_message(chat_id, f"Hai scritto: {text}")

        except Exception as e:
            print(f"Errore: {e}")
            time.sleep(5)

# Avvia bot in background quando parte Flask
import threading
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 10000))
    serve(app, host="0.0.0.0", port=port)
