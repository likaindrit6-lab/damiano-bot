
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot ONLINE Dami! Prova /live")

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot funziona! Pronostici 0-0 in arrivo domani!")

def main():
    if not TOKEN:
        print("MANCA BOT_TOKEN!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live))
    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
