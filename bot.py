import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")

API_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}

alerted_red=set(); alerted_hot=set(); alerted_dead=set(); last_scores={}

def get_live():
    try:
        r=requests.get(f"{API_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except: return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 DAMI BOT FINALE ATTIVO!\n🟥 Rosso <60'\n⚽ Goal\n🔥 Calda 6 tiri entro 60'\n💤 Morta max 3 tiri 50-60'")

async def check_all(context, manual_id=None):
    if not FOOTBALL_API_KEY: return
    lives=get_live()
    target=CHAT_ID or manual_id
    if not target: return
    for m in lives:
        fid=m["fixture"]["id"]; minute=m["fixture"]["status"]["elapsed"] or 0
        home=m["teams"]["home"]["name"]; away=m["teams"]["away"]["name"]
        hg=m["goals"]["home"] or 0; ag=m["goals"]["away"] or 0
        score=f"{hg}-{ag}"; name=f"{home} vs {away}"

        # GOAL
        if last_scores.get(fid) and last_scores[fid]!=score:
            await context.bot.send_message(chat_id=target, text=f"⚽ GOAL! {name}\n{minute}' -> {score}")
        last_scores[fid]=score

        # ROSSO
        if 0<minute<60 and fid not in alerted_red:
            try:
                ev=requests.get(f"{API_URL}/fixtures/events?fixture={fid}", headers=HEADERS, timeout=10).json().get("response",[])
                for e in ev:
                    if e["type"]=="Card" and "red" in e["detail"].lower() and e["time"]["elapsed"]<60:
                        await context.bot.send_message(chat_id=target, text=f"🟥 ROSSO {name}\n{minute}' {e['player']['name']}\n{score}")
                        alerted_red.add(fid)
            except: pass

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(lambda c: check_all(c), interval=45, first=15)
    print("BOT DAMI FINALE AVVIATO")
    app.run_polling()
if __name__=="__main__": main()
