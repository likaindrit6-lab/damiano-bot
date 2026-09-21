
import os, asyncio, aiohttp
from datetime import datetime
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
API = os.getenv("API_FOOTBALL_KEY")
CHAT = os.getenv("CHAT_ID")

print("Avvio V23...", flush=True)

async def check_loop(app):
    await asyncio.sleep(10)
    print("Loop pronto", flush=True)
    if CHAT:
        try:
            await app.bot.send_message(chat_id=int(CHAT), text="✅ V23 LIVE DAMI! Verde su Render! Ora gira ogni 90 sec")
            print("Messaggio LIVE inviato", flush=True)
        except Exception as e:
            print(f"Errore invio: {e}", flush=True)

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] CHECK 90s - V23 OK", flush=True)
            # test api se c'è chiave
            if API:
                try:
                    async with aiohttp.ClientSession() as s:
                        async with s.get("https://v3.football.api-sports.io/fixtures?live=all", headers={"x-apisports-key": API}, timeout=15) as r:
                            data = await r.json()
                            print(f"LIVE fixtures: {len(data.get('response',[]))}", flush=True)
                except Exception as e:
                    print(f"API error: {e}", flush=True)
        except Exception as e:
            print(f"Loop error: {e}", flush=True)
        await asyncio.sleep(90)

async def start(update, context):
    await update.message.reply_text("✅ V23 attivo!")

async def post_init(app):
    asyncio.create_task(check_loop(app))

if not TOKEN:
    print("ERRORE: BOT_TOKEN manca!", flush=True)
else:
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    print("Polling start...", flush=True)
    app.run_polling()
