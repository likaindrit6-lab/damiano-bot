
import os
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("🔥 DAMI BOT OK! SONO LIVE! FINALMENTE!")

async def live(update, context):
    await update.message.reply_text("Sono vivo!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live))
    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
