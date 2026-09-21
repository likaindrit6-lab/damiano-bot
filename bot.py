
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
            await app.bot.send_message(int(CHAT), "✅ V21 LIVE! Controllo ogni 90 sec ATTIVO. Ora non si spegne più.")
        except: pass
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] CHECK 90s", flush=True)
            if API:
                async with aiohttp.ClientSession() as s:
                    async with s.get("https://v3.football.api-sports.io/fixtures?live=all", headers={"x-apisports-key": API}) as r:
                        d = await r.json()
                        print(f"LIVE: {len(d.get('response',[]))}", flush=True)
        except Exception as e:
            print(f"Errore: {e}", flush=True)
        await asyncio.sleep(90)

async def start(u,c):
    await u.message.reply_text("✅ V21 attivo ogni 90 sec!")

async def post_init(app):
    asyncio.create_task(loop(app))

app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
