import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
CHAT_ID = os.getenv("CHAT_ID")

def api_get(url):
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    r = requests.get(url, headers=headers)
    return r.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot attivo! Usa /live")

async def live_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Proviamo 2 metodi per beccarle tutte
        data = api_get("https://v3.football.api-sports.io/fixtures?live=all")

        if data.get("errors"):
            await update.message.reply_text(f"❌ API BLOCK: {data['errors']}")
            print(f"API BLOCK: {data['errors']}")
            return

        live = data.get("response", [])

        # Se live=all dà 0, proviamo con il secondo metodo
        if len(live) == 0:
            data2 = api_get("https://v3.football.api-sports.io/fixtures?live=all&timezone=Europe/Rome")
            live = data2.get("response", [])

        if not live:
            await update.message.reply_text(f"📭 Nessuna live ora")
            return

        msg = f"📺 LIVE ORA REALE: {len(live)} partite\n\n"
        for f in live[:15]:
            home = f['teams']['home']['name']
            away = f['teams']['away']['name']
            goals_home = f['goals']['home']
            goals_away = f['goals']['away']
            minute = f['fixture']['status']['elapsed']
            msg += f"{minute}' {home} {goals_home}-{goals_away} {away}\n"

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")
        print(f"Errore: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live_debug))
    app.run_polling()

if __name__ == "__main__":
    main()
