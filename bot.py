import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Prende il token da Render (Environment Variables)
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot online! Scrivi /live")

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nessuna partita LIVE ora - bot funziona!")

def main():
    if not TOKEN:
        print("ERRORE: BOT_TOKEN mancante su Render!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live))
    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
