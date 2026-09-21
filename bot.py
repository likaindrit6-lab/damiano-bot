
import os, threading
from flask import Flask

TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID") or "").strip()
print(f"V28 TOKEN:{bool(TOKEN)}", flush=True)

web = Flask(__name__)
@web.route('/')
def home():
    return "V28 LIVE"

def start_bot():
    import asyncio
    from telegram.ext import ApplicationBuilder, CommandHandler
    async def start(update, context):
        await update.message.reply_text("V28 ACCESO!")
    async def loop(app):
        await asyncio.sleep(5)
        if CHAT:
            try:
                await app.bot.send_message(chat_id=int(CHAT), text="BOT ACCESO V28!")
            except Exception as e:
                print(e)
        while True:
            print("vivo 90s", flush=True)
            await asyncio.sleep(90)
    async def post_init(app):
        asyncio.create_task(loop(app))
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

threading.Thread(target=start_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    web.run(host="0.0.0.0", port=port)
