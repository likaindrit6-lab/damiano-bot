
import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import aiohttp
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
CHAT_ID = int(os.getenv("CHAT_ID", "0"))

logging.basicConfig(level=logging.INFO)

async def check_partite(app):
    print(f"[{datetime.now()}] CONTROLLO OGNI 90 SEC - SONO SVEGLIO", flush=True)
    # qui c'è il tuo controllo API-FOOTBALL
    # se trova CALDA/MORTA/ROSSO -> manda messaggio
    try:
        # ESEMPIO DI MESSAGGIO DI PROVA PER VEDERE SE GIRA
        # await app.bot.send_message(CHAT_ID, f"🔍 Controllo ore {datetime.now().strftime('%H:%M:%S')} - cerco partite...")
        pass
    except Exception as e:
        print(f"Errore controllo: {e}", flush=True)

async def loop_90s(app):
    await asyncio.sleep(10)
    await app.bot.send_message(CHAT_ID, "✅ V15 ATTIVO - Ora controllo OGNI 90 SECONDI da solo, anche se chiudi tutto!")
    while True:
        await check_partite(app)
        await asyncio.sleep(90)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot SVEGLIO! V15 controlla ogni 90 sec da solo. Non serve scrivere più /start.")

async def post_init(app):
    asyncio.create_task(loop_90s(app))

app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
