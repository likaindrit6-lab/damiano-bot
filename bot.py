import os, asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
import aiohttp
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
API = os.getenv("API_FOOTBALL_KEY")
CHAT = os.getenv("CHAT_ID")

async def loop(app):
    await asyncio.sleep(10)
    if CHAT:
        try:
            await app.bot.send_message(int(CHAT), "✅ DAMI V20 PULITO LIVE!\nControllo ogni 90 sec ATTIVO.\nOra non crasha più, puoi chiudere tutto.")
        except: pass

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] CHECK 90s", flush=True)
            if API:
                async with aiohttp.ClientSession() as s:
                    async with s.get("https://v3.football.api-sports.io/fixtures?live=all", headers={"x-apisports-key": API}) as r:
                        data = await r.json()
                        print(f"LIVE: {len(data.get('response',[]))}", flush=True)
        except Exception as e:
            print(f"Errore: {e}", flush=True)
        await asyncio.sleep(90)

async def start(update, context):
    await update.message.reply_text("✅ V20 attivo, giro ogni 90 sec!")

async def post_init(app):
    asyncio.create_task(loop(app))

app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
