
import os, asyncio, requests
from datetime import datetime, time
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

last_scores = {}
alerted_red = set()
alerted_calda = set()
alerted_morta = set()

def get_live():
    try:
        r = requests.get(API_URL + "/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except:
        return []

def get_stats(fid):
    try:
        r = requests.get(API_URL + "/fixtures/statistics?fixture=" + str(fid), headers=HEADERS, timeout=10).json().get("response", [])
        shots_on = 0
        corners = 0
        for team in r:
            for s in team.get("statistics", []):
                if s["type"] == "Shots on Goal":
                    shots_on += s["value"] or 0
                if s["type"] == "Corner Kicks":
                    corners += s["value"] or 0
        return shots_on, corners
    except:
        return 0, 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 DAMI BOT OK! Domani 09:00 schedina 1.70-1.80")

async def check_all(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID or not FOOTBALL_API_KEY:
        return
    for m in get_live():
        fid = m["fixture"]["id"]
        minute = m["fixture"]["status"]["elapsed"] or 0
        home = m["teams"]["home"]["name"]
        away = m["teams"]["away"]["name"]
        hg = m["goals"]["home"] or 0
        ag = m["goals"]["away"] or 0
        score = str(hg) + "-" + str(ag)
        if fid in last_scores and last_scores[fid]!= score:
            await context.bot.send_message(chat_id=CHAT_ID, text="⚽ GOAL " + str(minute) + "' " + home + " vs " + away + " -> " + score)
        last_scores[fid] = score
        if minute >= 70:
            shots_on, corners = get_stats(fid)
            if shots_on >= 8 and fid not in alerted_calda:
                await context.bot.send_message(chat_id=CHAT_ID, text="🔥 CALDA " + str(minute) + "' " + home + " vs " + away + " " + score)
                alerted_calda.add(fid)
            if score == "0-0" and shots_on <= 2 and fid not in alerted_morta:
                await context.bot.send_message(chat_id=CHAT_ID, text="💀 MORTA " + str(minute) + "' " + home + " vs " + away)
                alerted_morta.add(fid)
        if 0 < minute < 60 and fid not in alerted_red:
            try:
                ev = requests.get(API_URL + "/fixtures/events?fixture=" + str(fid), headers=HEADERS, timeout=10).json().get("response", [])
                for e in ev:
                    if e["type"] == "Card" and "red" in e["detail"].lower() and e["time"]["elapsed"] < 60:
                        await context.bot.send_message(chat_id=CHAT_ID, text="🟥 ROSSO " + str(minute) + "' " + home + " vs " + away + " " + score)
                        alerted_red.add(fid)
                        break
            except:
                pass

async def schedina_mattutina(context: ContextTypes.DEFAULT_TYPE):
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        fixtures = requests.get(API_URL + "/fixtures?date=" + today, headers=HEADERS, timeout=15).json().get("response", [])[:15]
        schedina = []
        quota_tot = 1.0
        for f in fixtures:
            if len(schedina) >= 6:
                break
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            ora = f["fixture"]["date"][11:16]
            schedina.append(ora + " " + home + " vs " + away + " - Over 0.5 @ 1.10")
            quota_tot = quota_tot * 1.10
        text = "🎫 SCHEDINA DAMI - " + today + "\nQuota 1.70-1.80\n\n"
        for i, s in enumerate(schedina):
            text += str(i+1) + ". " + s + "\n"
        text += "\nTOT: " + str(round(quota_tot,2))
        await context.bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        await context.bot.send_message(chat_id=CHAT_ID, text="Schedina errore: " + str(e))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(check_all, interval=60, first=15)
    app.job_queue.run_daily(schedina_mattutina, time=time(7,0,0))
    app.run_polling()

if __name__ == "__main__":
    main()
