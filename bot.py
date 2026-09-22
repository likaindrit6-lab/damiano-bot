
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
# legge entrambi i nomi per non sbagliare
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY") or os.getenv("API_FOOTBALL_KEY")
CHAT_ID = os.getenv("CHAT_ID")

API_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY} if FOOTBALL_API_KEY else {}

last_scores = {}
alerted_red = set()

def get_live():
    try:
        r = requests.get(f"{API_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except:
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔥 DAMI BOT ATTIVO!\nID {CHAT_ID} collegato\n🟥 Rosso <60'\n⚽ Goal\nPronto!")

async def check_all(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID or not FOOTBALL_API_KEY:
        return
    try:
        for m in get_live():
            fid = m["fixture"]["id"]
            minute = m["fixture"]["status"]["elapsed"] or 0
            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]
            hg = m["goals"]["home"] or 0
            ag = m["goals"]["away"] or 0
            score = f"{hg}-{ag}"

            if fid in last_scores and last_scores[fid]!= score:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"⚽ GOAL! {home} vs {away} {minute}' {score}")
            last_scores[fid] = score

            if 0 < minute < 60 and fid not in alerted_red:
                try:
                    ev = requests.get(f"{API_URL}/fixtures/events?fixture={fid}", headers=HEADERS, timeout=10).json().get("response", [])
                    for e in ev:
                        if e["type"] == "Card" and "red" in e["detail"].lower() and e["time"]["elapsed"] < 60:
                            await context.bot.send_message(chat_id=CHAT_ID, text=f"🟥 ROSSO {minute}' {home} vs {away} {score}")
                            alerted_red.add(fid)
                            break
                except:
                    pass
    except:
        pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(check_all, interval=45, first=15)
    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
