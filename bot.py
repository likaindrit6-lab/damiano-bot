
import os, asyncio, threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
import aiohttp
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
API = os.getenv("API_FOOTBALL_KEY")
CHAT = os.getenv("CHAT_ID")

# Trucco per Render Web Service
app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "V25 LIVE"

def run_web():
    port = int(os.getenv("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

async def loop_90s(app):
    await asyncio.sleep(10)
    print("Loop V25 partito", flush=True)
    if CHAT:
        try:
            await app.bot.send_message(chat_id=int(CHAT), text="✅ V25 VERDE DAMI! Render non lo spegne più!")
        except Exception as e:
            print(e)
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] CHECK 90s V25", flush=True)
            if API:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get("https://v3.football.api-sports.io/fixtures?live=all", headers={"x-apisports-key": API}, timeout=15) as r:
                            j = await r.json()
                            print(f"Live: {len(j.get('response',[]))}", flush=True)
                except Exception as e:
                    print(f"API err: {e}", flush=True)
        except Exception as e:
            print(f"Loop err: {e}", flush=True)
        await asyncio.sleep(90)

async def start(update, context):
    await update.message.reply_text("✅ V25 attivo!")

async def post_init(application):
    asyncio.create_task(loop_90s(application))

print("Avvio V25...", flush=True)
app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
