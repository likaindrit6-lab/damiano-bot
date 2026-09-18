
import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot LIVE 0-0 - 30s OK!"

TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("API_KEY")
CHATS = set()
INVIATE = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Bot LIVE attivo! Controllo ogni 30 secondi le partite 0-0 dal 5' al 40'")

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHATS.add(update.effective_chat.id)
    await update.message.reply_text("🔍 Modalità LIVE 30s attiva! Ti avviso io.")

async def check(context: ContextTypes.DEFAULT_TYPE):
    try:
        if not API_KEY or not CHATS:
            return
        url = "https://v3.football.api-sports.io/fixtures?live=all"
        headers = {"x-apisports-key": API_KEY}
        r = requests.get(url, headers=headers, timeout=10).json()
        for f in r.get("response", []):
            try:
                if f['goals']['home'] == 0 and f['goals']['away'] == 0:
                    elapsed = f['fixture']['status']['elapsed']
                    if elapsed and 5 <= elapsed <= 40:
                        fid = f['fixture']['id']
                        if fid not in INVIATE:
                            home = f['teams']['home']['name']
                            away = f['teams']['away']['name']
                            msg = f"🔔 0-0 LIVE al {elapsed}'\n{home} vs {away}\nControllo ogni 30s"
                            for cid in list(CHATS):
                                try:
                                    await context.bot.send_message(chat_id=cid, text=msg)
                                except: pass
                            INVIATE.add(fid)
            except: continue
        if len(INVIATE) > 300:
            INVIATE.clear()
    except Exception as e:
        print(f"Errore check: {e}")

def main():
    a = Application.builder().token(TOKEN).build()
    a.add_handler(CommandHandler("start", start))
    a.add_handler(CommandHandler("live", live))
    # QUESTO È IL 30 SECONDI CHE VOLEVI
    a.job_queue.run_repeating(check, interval=30, first=5)
    a.run_polling()

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
main()
