
import os, threading
from flask import Flask

TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID") or "").strip()

print(f"V30 TOKEN:{bool(TOKEN)} CHAT:{bool(CHAT)}", flush=True)

web = Flask(__name__)

@web.route('/')
def home():
    return f"V30 LIVE - TOKEN={bool(TOKEN)}"

def start_bot():
    import asyncio
    from telegram.ext import ApplicationBuilder, CommandHandler
    
    async def cmd_start(update, context):
        await update.message.reply_text("Bot V30 acceso Dami!")

    async def loop(app):
        await asyncio.sleep(5)
        print("V30 loop check", flush=True)
        if CHAT:
            try:
                await app.bot.send_message(chat_id=int(CHAT), text="BOT V30 ACCESO Dami! Tutto OK ✅")
                print("V30 messaggio inviato", flush=True)
            except Exception as e:
                print(f"V30 errore invio: {e}", flush=True)
        while True:
            print("vivo 90s", flush=True)
            await asyncio.sleep(90)

    async def post_init(app):
        asyncio.create_task(loop(app))

    try:
        print("V30 avvio polling...", flush=True)
        app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
        app.add_handler(CommandHandler("start", cmd_start))
        app.run_polling()
    except Exception as e:
        print(f"V30 CRASH: {e}", flush=True)

threading.Thread(target=start_bot, daemon=True).start()

if __name__ == "__main__":
    web.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
