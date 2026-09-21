
import os
import time
import threading
from flask import Flask
import telebot

# --- FIX PER RENDER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Live!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

# --- BOT TELEGRAM ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Dami sono ONLINE! 🔥 Il bot funziona!")

@bot.message_handler(commands=['live'])
def live(message):
    bot.reply_to(message, "Funzione live pronta!")

print("Bot partito...")
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Errore: {e}")
        time.sleep(5)
