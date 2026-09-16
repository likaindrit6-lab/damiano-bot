
import os, threading, requests, time
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): 
    return "Bot 0-0 LIVE! Damiano"

TOKEN = os.environ.get("BOT_TOKEN")
CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Bot ATTIVO Damiano! Ti avviserò su 0-0!")

async def check_matches(app_bot):
    while True:
        try:
            # Qui va la tua logica di controllo partite 0-0
            # Esempio: se trova una partita te lo manda
            print("Controllo partite...")
            # for chat_id in list(CHATS):
            #    await app_bot.bot.send_message(chat_id, "Test segnale 0-0")
        except Exception as e:
            print(f"Errore check: {e}")
        time.sleep(60)

def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # Avvia controllo in background
    def start_checker():
        time.sleep(5)
        import asyncio
        asyncio.run(check_matches(application))
    
    threading.Thread(target=start_checker, daemon=True).start()
    
    print("Bot Telegram avviato!")
    application.run_polling(drop_pending_updates=True)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
