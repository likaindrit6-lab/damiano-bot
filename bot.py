
import os
import logging
import asyncio
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Prende la chiave con QUALSIASI nome tu abbia usato
API_KEY = os.getenv("API_FOOTBALL_KEY") or os.getenv("API_FOOTBALL") or os.getenv("FOOTBALL_API_KEY") or os.getenv("API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN mancante!")
if not API_KEY:
    raise ValueError("API FOOTBALL mancante su Render! Controlla Environment")

CHAT_ID = None
ALERTED_RED = set()
ALERTED_HOT = set()
ALERTED_DEAD = set()
ALERTED_GOAL = set()

HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

def api_call(endpoint, params={}):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200:
            return r.json().get("response", [])
        logger.error(f"API {r.status_code}: {r.text[:200]}")
        return []
    except Exception as e:
        logger.error(f"Errore API: {e}")
        return []

async def send(app, text):
    if CHAT_ID:
        try:
            await app.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Errore TG: {e}")

async def live_loop(app):
    logger.info("LOOP MONDIALE PARTITO - 90 sec - TUTTI I CAMPIONATI")
    while True:
        try:
            lives = api_call("fixtures", {"live": "all"})
            logger.info(f"Live trovate: {len(lives)}")

            for m in lives:
                fid = m.get("fixture", {}).get("id")
                minute = m.get("fixture", {}).get("status", {}).get("elapsed") or 0
                if not fid or minute == 0: continue

                league = m.get("league", {})
                teams = m.get("teams", {})
                goals = m.get("goals", {})
                
                events = api_call("fixtures/events", {"fixture": fid})
                stats = api_call("fixtures/statistics", {"fixture": fid})

                # Calcolo tiri in porta
                shots = 0
                if stats:
                    for ts in stats:
                        for s in ts.get("statistics", []):
                            if "Shots on Goal" in s.get("type",""):
                                shots += int(s.get("value") or 0)

                # 1. ROSSO < 70
                for ev in events:
                    if ev.get("type") == "Card" and "red" in str(ev.get("detail","")).lower():
                        ev_min = ev.get("time",{}).get("elapsed", 100)
                        if ev_min < 70 and fid not in ALERTED_RED:
                            ALERTED_RED.add(fid)
                            await send(app, f"🟥 **ROSSO PRIMA 70°!**\n\n🏆 {league.get('name')} {league.get('country')}\n⚽️ {teams.get('home',{}).get('name')} vs {teams.get('away',{}).get('name')}\n⏱️ {ev_min}° - {ev.get('player',{}).get('name')}\n💰 PUNTA!")

                # 2. CALDA 6 tiri entro 60
                if minute <= 60 and shots >= 6 and fid not in ALERTED_HOT:
                    ALERTED_HOT.add(fid)
                    await send(app, f"🔥 **CALDA! 6 tiri entro 60°**\n\n🏆 {league.get('name')}\n⚽️ {teams.get('home',{}).get('name')} {goals.get('home',0)}-{goals.get('away',0)} {teams.get('away',{}).get('name')}\n⏱️ {minute}° - Tiri: {shots}\n👉 GOL in arrivo!")

                # 3. GOL dopo calda
                if fid in ALERTED_HOT and fid not in ALERTED_GOAL:
                    for ev in events:
                        if ev.get("type") == "Goal":
                            ALERTED_GOAL.add(fid)
                            await send(app, f"⚽️ **GOL DOPO CALDA!**\n\n🏆 {league.get('name')}\n⚽️ {teams.get('home',{}).get('name')} {goals.get('home')}-{goals.get('away')} {teams.get('away',{}).get('name')}\n⏱️ {ev.get('time',{}).get('elapsed')}° {ev.get('player',{}).get('name')}")
                            break

                # 4. MORTA 3 tiri al 60° -> UNDER
                if 60 <= minute <= 65 and shots <= 3 and fid not in ALERTED_DEAD:
                    tot = (goals.get('home') or 0) + (goals.get('away') or 0)
                    if tot <= 1:
                        ALERTED_DEAD.add(fid)
                        await send(app, f"💀 **MORTA / DEBOLE - UNDER**\n\n🏆 {league.get('name')}\n⚽️ {teams.get('home',{}).get('name')} {goals.get('home')}-{goals.get('away')} {teams.get('away',{}).get('name')}\n⏱️ {minute}° - Tiri: {shots}\n💡 Consiglio: **UNDER 2.5**")

        except Exception as e:
            logger.error(f"Loop error: {e}")

        await asyncio.sleep(90)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    await update.message.reply_text("✅ BOT MONDIALE LIVE ATTIVO!\n🌍 Tutti i campionati\n⏱️ Ogni 90 sec\n🟥 Rosso <70\n🔥 Calda 6 tiri\n💀 Morta 3 tiri = Under\n\nTi avviso io Dami!", parse_mode='Markdown')

def main():
    print("BOT DAMI LIVE MONDIALE AVVIATO")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedina", start))

    async def startup(a):
        asyncio.create_task(live_loop(a))
    
    app.post_init = startup
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
