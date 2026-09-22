
import os
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("🔥 DAMI BOT OK! 09:00-01:00 attivo")

async def live(update, context):
    await update.message.reply_text("Sono vivo Dami! Nessun LIVE ora")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("live", live))
app.run_polling()
