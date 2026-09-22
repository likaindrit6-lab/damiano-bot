
import os, asyncio, requests
# FIX per Render Python 3.14
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY") or os.getenv("API_FOOTBALL_KEY")
CHAT_ID = os.getenv("CHAT_ID")

API_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY} if FOOTBALL_API_KEY else {}

last_scores={}; alerted_red=set()

def get_live():
    try:
        r=requests.get(f"{API_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except: return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔥 DAMI BOT ATTIVO!\nID {CHAT_ID}\nPronto!")

async def check_all(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID or not FOOTBALL_API_KEY: return
    try:
        for m in get_live():
            fid=m["fixture"]["id"]; minute=m["fixture"]["status"]["elapsed"] or 0
            home=m["teams"]["home"]["name"]; away=m["teams"]["away"]["name"]
            hg=m["goals"]["home"] or 0; ag=m["goals"]["away"] or 0
            score=f"{hg}-{ag}"
            if fid in last_scores and last_scores[fid]!=score:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"⚽ GOAL {home} vs {away} {minute}' {score}")
            last_scores[fid]=score
    except: pass

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(check_all, interval=45, first=15)
    app.run_polling()

if __name__=="__main__": main()
