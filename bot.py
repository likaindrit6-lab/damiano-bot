
import os
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("🔥 DAMI BOT OK! SONO LIVE! Ora funziona!")

async def live(update, context):
    await update.message.reply_text("Sono vivo Dami!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live))
    app.run_polling()

if __name__ == "__main__":
    main()
