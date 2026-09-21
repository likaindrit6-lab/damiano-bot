
import os, time, requests, logging
from datetime import datetime
import telegram
from telegram.ext import Application, CommandHandler

# LEGGE SIA NOMI VECCHI CHE NUOVI - COSI' NON SI BLOCCA PIU'
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY") or os.getenv("API_KEY")

# LOG DI CONTROLLO
print(f"CHECK ENV: API_KEY={'OK' if API_KEY else 'MANCANTE'} BOT_TOKEN={'OK' if BOT_TOKEN else 'MANCANTE'} CHAT_ID={CHAT_ID}", flush=True)

logging.basicConfig(level=logging.INFO)

# Cancella webhook se rimasto
if BOT_TOKEN:
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook", timeout=10)
        print("DELETE WEBHOOK: OK", flush=True)
    except Exception as e:
        print(f"DELETE WEBHOOK ERROR: {e}", flush=True)

async def start(update, context):
    await update.message.reply_text("✅ BOT SBLOCCATO! Sono online Dami!\nUsa /scan per cercare partite.")

async def scan(update, context):
    await update.message.reply_text("🔍 Scansione partite in corso...")
    # qui va la tua logica di scansione
    # ...

def main():
    if not BOT_TOKEN:
        print("ERRORE: TELEGRAM_BOT_TOKEN non trovato!", flush=True)
        while True:
            time.sleep(60)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    
    print("HANDLE COMMANDS PARTITO - IN ATTESA SU TELEGRAM", flush=True)
    app.run_polling()

if __name__ == "__main__":
    main()
