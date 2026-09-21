
import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import aiohttp
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
CHAT_ID_STR = os.getenv("CHAT_ID", "0")
try:
    CHAT_ID = int(CHAT_ID_STR)
except:
    CHAT_ID = 0

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

async def check_live():
    # 1 chiamata ogni 90 sec = usi circa 960 chiamate al giorno, ne hai 7200
    if not API_KEY:
        return
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"x-apisports-key": API_KEY}
            async with session.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers) as r:
                data = await r.json()
                live = len(data.get("response", []))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Controllo 90sec - Live: {live} partite", flush=True)
                return data
    except Exception as e:
        print(f"Errore API: {e}", flush=True)

async def loop_90s(app):
    await asyncio.sleep(5)
    if CHAT_ID != 0:
        try:
            await app.bot.send_message(CHAT_ID, "✅ DAMI V16 ATTIVO! Controllo OGNI 90 SECONDI iniziato. Ora puoi chiudere tutto!")
        except Exception as e:
            print(f"Errore invio avvio: {e}", flush=True)
    
    while True:
        await check_live()
        await asyncio.sleep(90)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Sono sveglio Dami! V16 gira ogni 90 sec. Non serve che scrivi più /start")

async def post_init(app):
    asyncio.create_task(loop_90s(app))

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("MANCA BOT_TOKEN su Render!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
        app.add_handler(CommandHandler("start", start))
        print("Bot in avvio...", flush=True)
        app.run_polling()
