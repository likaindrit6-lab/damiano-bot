import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler

# Prende il token da Render
TOKEN = os.getenv("BOT_TOKEN")

# --- Parte finta sito web per Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot di Damiano acceso!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Parte Telegram ---
async def start(update, context):
    await update.message.reply_text("Ciao Damiano! Bot funziona! ✅")

def main():
    # Fa partire il sito in sottofondo
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Fa partire Telegram
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("Bot avviato...")
    application.run_polling()

if __name__ == '__main__':
    main()
