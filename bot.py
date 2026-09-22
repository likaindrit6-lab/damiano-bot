
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurazione log
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

print("BOT DAMI LIVE + SCHEDINA AVVIATO")
print(f"Token presente: {bool(BOT_TOKEN)}")
print(f"API Key presente: {bool(API_FOOTBALL_KEY)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Ciao Dami! Bot ONLINE e funzionante! Scrivi /schedina")

async def schedina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚽ Funzione schedina in arrivo... bot live!")

def main():
    if not BOT_TOKEN:
        print("ERRORE: BOT_TOKEN non trovato nelle Environment Variables!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedina", schedina))
    
    print("Polling avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
