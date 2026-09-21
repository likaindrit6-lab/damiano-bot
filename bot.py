
import os
import threading
from flask import Flask
import telebot

# Fix per Render - tiene vivo il servizio
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Live! Damiano Bot OK"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# Bot Telegram
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "DAMI SONO ONLINE! 🔥 Il bot funziona alla grande!")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, f"Ricevuto: {message.text}")

print("Bot Damiano partito correttamente...")
bot.infinity_polling()
