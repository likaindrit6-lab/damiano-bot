
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
print("BOT DAMI LIVE + SCHEDINA AVVIATO")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 DAMI CI SIAMO! Bot online! Funziona!")

async def schedina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚽ Schedina pronta Dami!")

def main():
    if not BOT_TOKEN:
        print("ERRORE: BOT_TOKEN mancante su Render")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedina", schedina))
    print("Polling avviato - BOT PRONTO")
    app.run_polling()

if __name__ == "__main__":
    main()
