
import os, threading, time
from flask import Flask
from datetime import datetime

print("V27 START", flush=True)

web = Flask(__name__)
@web.route('/')
def home():
    return "V27 LIVE DAMI"

def run_web():
    port = int(os.getenv("PORT", 10000))
    web.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

try:
    import asyncio, aiohttp
    from telegram.ext import ApplicationBuilder, CommandHandler

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    API = os.getenv("API_FOOTBALL_KEY")
    CHAT = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

    print(f"TOKEN trovato: {bool(TOKEN)}", flush=True)

    if not TOKEN:
        while True:
            time.sleep(60)

    async def loop_90s(app):
        await asyncio.sleep(10)
        if CHAT:
            try:
                await app.bot.send_message(chat_id=int(CHAT), text="✅ V27 VERDE DAMI!")
            except:
                pass
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] CHECK 90s", flush=True)
            await asyncio.sleep(90)

    async def start(update, context):
        await update.message.reply_text("✅ V27 verde!")

    async def post_init(app):
        asyncio.create_task(loop_90s(app))

    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

except Exception as e:
    print(f"ERRORE: {e}", flush=True)
    import traceback
    traceback.print_exc()
    while True:
        time.sleep(60)
