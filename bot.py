
import os
import time
import requests
from threading import Thread
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 0-0 Damiano ONLINE!"

def send_telegram(text, chat_id=None):
    try:
        cid = chat_id or CHAT_ID
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": cid, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
        print(f"Inviato a {cid}: {text[:50]}")
    except Exception as e:
        print(f"Errore invio: {e}")

# --- GESTIONE COMANDI MENU ---
def handle_commands():
    offset = 0
    print("Polling comandi Telegram avviato...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=20"
            r = requests.get(url, timeout=25).json()
            
            for update in r.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "")
                chat = str(message.get("chat", {}).get("id", ""))

                if not text.startswith("/"):
                    continue

                print(f"Comando ricevuto: {text} da {chat}")

                if text.startswith("/start"):
                    send_telegram("⚽ *Bot 0-0 Damiano ACCESO!*\n\nCiao! Sono online.\n\nUsa il Menu qui sotto:\n/live - Partite di ora\n/gol - Ultimi gol\n/help - Aiuto\n\nTi avviso io appena c'è un gol!", chat)
                elif text.startswith("/help"):
                    send_telegram("📖 *HELP*\n\n/start - Accendi il bot\n/live - Vedi le partite live\n/gol - Ultimi gol segnati\n\nPer ora il bot ti avvisa in automatico dei gol. I comandi /live e /gol li colleghiamo alla Serie A nel prossimo step!", chat)
                elif text.startswith("/live"):
                    send_telegram("🔴 *Partite Live (TEST)*\n\nAl momento sto monitorando:\nInter 0-0 Milan (12')\nJuve 1-0 Napoli (45')\n\nAppena c'è un gol ti avviso io qui! Fra poco colleghiamo i dati reali.", chat)
                elif text.startswith("/gol"):
                    send_telegram("⚽ *Ultimo Gol (TEST)*\n\nJuve 1-0 Napoli\nGol di Vlahovic al 45'!", chat)

        except Exception as e:
            print(f"Errore polling: {e}")
            time.sleep(5)

def bot_logic():
    time.sleep(3)
    send_telegram("✅ *Bot 0-0 Damiano AGGIORNATO!*\n\nOra il menu funziona!\nProva a cliccare su Menu > start")
    
    # Avvia il controllo dei comandi
    Thread(target=handle_commands, daemon=True).start()

    # Qui poi mettiamo il controllo gol veri
    while True:
        time.sleep(60)

if __name__ == "__main__":
    Thread(target=bot_logic, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
