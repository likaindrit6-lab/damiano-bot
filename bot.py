import os, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import aiohttp
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
CHAT_ID = int(os.getenv("CHAT_ID", "0") or 0)

async def controllo_90sec(app):
    print("AVVIO LOOP 90 SEC", flush=True)
    await asyncio.sleep(5)
    try:
        await app.bot.send_message(CHAT_ID, "✅ DAMI V17 FIXATO! Ora controllo OGNI 90 SECONDI. Hai 7200 chiamate, le uso tutte. Puoi chiudere tutto!")
    except Exception as e:
        print(f"Errore invio start: {e}", flush=True)

    while True:
        try:
            if API_KEY:
                async with aiohttp.ClientSession() as s:
                    async with s.get("https://v3.football.api-sports.io/fixtures?live=all", headers={"x-apisports-key": API_KEY}) as r:
                        j = await r.json()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] CHECK 90s -> Live: {len(j.get('response',[]))}", flush=True)
        except Exception as e:
            print(f"Errore check: {e}", flush=True)
        await asyncio.sleep(90)

async def start(update, context):
    await update.message.reply_text("✅ V17 attivo ogni 90 sec!")

async def post_init(app):
    asyncio.create_task(controllo_90sec(app))

app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
