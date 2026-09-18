import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot O-O LIVE!"

TOKEN = os.environ.get("BOT_TOKEN")
CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Bot ATTIVO! Ti avviserò per le partite 0-0 dal 70' all'82'")

def get_live():
    try:
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard", timeout=10)
        out=[]
        for ev in r.json().get('events',[]):
            comp=ev['competitions'][0]
            try:
                clock = comp['status']['displayClock']
                minuto=int(clock.split("'")[0])
            except:
                continue
            if 70 <= minuto <= 82:
                home=comp['competitors'][0]
                away=comp['competitors'][1]
                if home['score']=='0' and away['score']=='0':
                    out.append(f"🔥 {home['team']['displayName']} 0-0 {away['team']['displayName']} {minuto}'")
        return out
    except:
        return []

async def check(context: ContextTypes.DEFAULT_TYPE):
    partite=get_live()
    for cid in list(CHATS):
        for p in partite:
            try:
                await context.bot.send_message(chat_id=cid, text=p)
            except:
                pass

def main():
    a = Application.builder().token(TOKEN).build()
    a.add_handler(CommandHandler("start", start))
    a.job_queue.run_repeating(check, interval=60, first=10)
    a.run_polling(drop_pending_updates=True)

def run_flask():
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
