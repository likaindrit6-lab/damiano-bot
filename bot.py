import os
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import NetworkError, Conflict

CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

alerted_calda = set()
alerted_morta = set()
alerted_red = set()
bet_attive = set()
last_scores = {}

def get_live():
    headers = {"x-apisports-key": FOOTBALL_API_KEY}
    r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=20)
    return r.json().get("response", [])

def get_stats(fid):
    try:
        headers = {"x-apisports-key": FOOTBALL_API_KEY}
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=headers, timeout=20)
        data = r.json().get("response", [])
        shots = 0
        for team in data:
            for s in team.get("statistics", []):
                if s["type"] == "Shots on Goal":
                    shots += int(s["value"] or 0)
        return shots, 0
    except:
        return 0, 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 DAMI BOT OK! Domani 09:00 schedina 1.70-1.80 - Bot live e fixato!")

async def check_all(context):
    if not CHAT_ID or not FOOTBALL_API_KEY:
        return
    print("Checking live...")
    try:
        live = get_live()
    except Exception as e:
        print(f"Errore get_live: {e}")
        return
    for m in live:
        try:
            fid = m["fixture"]["id"]
            minute = m["fixture"]["status"]["elapsed"] or 0
            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]
            score = f"{m['goals']['home'] or 0}-{m['goals']['away'] or 0}"
            shots_on, _ = get_stats(fid)

            if shots_on >= 6 and fid not in alerted_calda:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"🔥 CALDA {minute}' {home} vs {away} {score} - {shots_on} tiri in porta - PUNTA")
                alerted_calda.add(fid)
                bet_attive.add(fid)
                last_scores[fid] = score

            if 44 <= minute <= 48 and shots_on <= 3 and fid not in alerted_morta and fid not in alerted_calda:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"💀 MORTA HT {home} vs {away} {score} - solo {shots_on} tiri")
                alerted_morta.add(fid)

            if fid in bet_attive:
                old = last_scores.get(fid)
                if old and old!= score:
                    await context.bot.send_message(chat_id=CHAT_ID, text=f"⚽ GOAL! {home} vs {away} ora {score} - VINTA")
                    bet_attive.remove(fid)
                last_scores[fid] = score
        except:
            continue

async def error_handler(update, context):
    err = context.error
    print(f"ERRORE: {err} - riprovo in 10s")
    if "ReadError" in str(err) or "NetworkError" in str(err) or isinstance(err, (NetworkError, Conflict)):
        await asyncio.sleep(10)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_error_handler(error_handler)
    app.job_queue.run_repeating(check_all, interval=60, first=10)
    print("Bot avviato - fix NetworkError attivo")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False, stop_signals=None)
