
import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Bot 0-0 LIVE!"

TOKEN = os.environ.get("BOT_TOKEN")
CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Bot 0-0 AVVIATO!\nControllo ogni 5 min 🔥\nTi avviso al 70-82' se è 0-0")

def get_live():
    try:
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard", timeout=10).json()
        out=[]
        for ev in r.get('events',[]):
            comp=ev['competitions'][0]
            try:
                minuto=int(comp['status'].get('displayClock','0').split("'")[0])
            except: continue
            if 70 <= minuto <= 82:
                home=comp['competitors'][0]
                away=comp['competitors'][1]
                if home['score']=='0' and away['score']=='0':
                    out.append(f"🔥 {home['team']['displayName']} vs {away['team']['displayName']}\n⏱️ {minuto}' - ANCORA 0-0")
        return out
    except: return []

async def check(context: ContextTypes.DEFAULT_TYPE):
    partite=get_live()
    for cid in list(CHATS):
        for p in partite:
            try: await context.bot.send_message(chat_id=cid, text=p)
            except: pass

def main():
    a = Application.builder().token(TOKEN).build()
    a.add_handler(CommandHandler("start", start))
    a.job_queue.run_repeating(check, interval=300, first=15)
    a.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000))), daemon=True).start()
    main()
