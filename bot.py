
import os
import threading
import time
from flask import Flask
import telebot

print("--- BOT V34 AVVIO DAMI ---")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)
@app.route('/')
def home():
    return "BOT V34 ONLINE"

def start_bot():
    if not TOKEN:
        print("ERRORE: TOKEN mancante!")
        return
    bot = telebot.TeleBot(TOKEN, threaded=False)

    @bot.message_handler(commands=['start'])
    def cmd_start(m):
        bot.reply_to(m, "BOT V34 ACCESO Dami! Funziona!")

    try:
        if CHAT_ID:
            bot.send_message(CHAT_ID, "BOT V34 ACCESO Dami! Se leggi questo, abbiamo vinto!")
            print("Messaggio inviato OK!")
    except Exception as e:
        print(f"Errore invio: {e}")

    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Polling errore: {e}")
            time.sleep(5)

if TOKEN:
    threading.Thread(target=start_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
