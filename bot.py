
import os
import timeimport os
import threading
from flask import Flask
import telebot
import time

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
    bot.reply_to(message, "Dami sono ONLINE! 🔥 Il bot funziona! Mandami /live per le partite")

@bot.message_handler(commands=['live'])
def live(message):
    bot.reply_to(message, "Funzione live attiva! Ora ti mando i gol")

print("Bot partito...")
while True:
    try:
        bot.polling(none_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"Errore: {e}")
        time.sleep(5)
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
                    send_telegram("🔴 *Partite Live (TEST)*\n\nAl momento sto monitorando:\nInter 0-0 Milan (12')\nJuve 1-0 Napoli (45')\n\nAppena c'è un gol 
