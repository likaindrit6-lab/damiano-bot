import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Bot 0-0 LIVE!"

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_FILE = "chats.txt"

# Carica chat
def load_chats():
    try:
        with open(CHAT_FILE, "r") as f:
            return set(f.read().splitlines())
    except: return set()

def save_chat(chat_id):
    chats = load_chats()
    if str(chat_id) not in chats:
        with open(CHAT_FILE, "a") as f:
            f.write(f"{chat_id}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat(update.effective_chat.id)
    await update.message.reply_text("✅ Bot 0-0 AVVIATO!\nControllo ogni 5 min 🔥")

def get_live_0_0():
    try:
        # API ESPN gratis - partite live
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        r = requests.get(url, timeout=10).json()
        risultati = []
        for event in r.get('events', []):
            comp = event['competitions'][0]
            status = comp['status']['type']['description']
            clock = comp['status'].get('displayClock', '0')
            home = comp['competitors'][0]
            away = comp['competitors'][1]
            # Prendi minuti
            try:
                minuto = int(clock.split("'")[0].replace(" ",""))
            except:
                minuto = 0

            if 70 <= minuto <= 82 and home['score'] == '0' and away['score'] == '0':
                leg = event.get('league','')
                risultati.append(f"🔥 {home['team']['displayName']} vs {away['team']['displayName']}\n🏆 {comp.get('type','')}\n⏱️ {minuto}' - ANCORA 0-0")
        return risultati
    except Exception as e:
        print(f"Errore: {e}")
        return []

async def check_job(context: ContextTypes.DEFAULT_TYPE):
    partite = get_live_0_0()
    if not partite:
        return
    chats = load_chats()
    for chat_id in chats:
        for p in partite:
            try:
                await context.bot.send_message(chat_id=chat_id, text=p)
            except:
                pass

def main():
    a = Application.builder().token(TOKEN).build()
    a.add_handler(CommandHandler("start", start))
    # Controllo ogni 5 minuti = 300 secondi
    a.job_queue.run_repeating(check_job, interval=300, first=15)
    a.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000))), daemon=True).start()
    main()
