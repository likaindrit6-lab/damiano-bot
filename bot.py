
import os
import threading
from flask import Flask
import telebot

app = Flask(__name__)
@app.route('/')
def home():
    return "OK"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "DAMI SONO ONLINE! 🔥")

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    bot.reply_to(m, "Funziona!")

print("Bot partito")
bot.infinity_polling()
