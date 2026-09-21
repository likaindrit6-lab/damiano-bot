
import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V35.2 ONLINE - FIX SYNTAX", 200

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")

print("Avvio V35.2...")
print(f"TOKEN ok: {bool(TELEGRAM_TOKEN)}")
print(f"API KEY ok: {bool(API_FOOTBALL_KEY)}")

def check_partite():
    while True:
        try:
            if not API_FOOTBALL_KEY:
                print("Manca API_FOOTBALL_KEY su Render, aspetto 90 sec")
                time.sleep(90)
                continue

            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            url = "https://v3.football.api-sports.io/fixtures?live=all"
            r = requests.get(url, headers=headers, timeout=15)
            data = r.json()
            fixtures = data.get("response", [])
            print(f"LIVE trovate: {len(fixtures)} - consumo 1 token")
            
        except Exception as e:
            print(f"Errore: {e}")
        
        time.sleep(90)

def run_bot():
    try:
        import telebot
        if not TELEGRAM_TOKEN:
            print("Manca TELEGRAM_TOKEN, Flask resta ON")
            return
        bot = telebot.TeleBot(TELEGRAM_TOKEN)

        @bot.message_handler(commands=['start'])
        def start(m):
            bot.reply_to(m, f"V35.2 ATTIVO! ChatID: {m.chat.id} - LIVE 24/7")

        bot.infinity_polling()
    except Exception as e:
        print(f"Errore Telegram: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=check_partite, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
