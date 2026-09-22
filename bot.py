
import os, logging, asyncio, requests, time
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY") or os.getenv("API_FOOTBALL") or os.getenv("FOOTBALL_API_KEY") or os.getenv("API_KEY")

CHAT_ID_FILE = "/tmp/chat_id.txt"
CHAT_ID = None
ALERTED_RED, ALERTED_HOT, ALERTED_DEAD = set(), set(), set()

# Carica chat salvata
if os.path.exists(CHAT_ID_FILE):
    try: CHAT_ID = int(open(CHAT_ID_FILE).read())
    except: pass

HEADERS = {"x-apisports-key": API_KEY} if API_KEY else {}
BASE_URL = "https://v3.football.api-sports.io"

def api_call(endpoint, params={}):
    if not API_KEY: return []
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200: return r.json().get("response", [])
        logger.error(f"API {r.status_code}")
        return []
    except Exception as e:
        logger.error(f"API err {e}"); return []

async def send(app, text):
    if CHAT_ID:
        try: await app.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
        except Exception as e: logger.error(f"TG: {e}")

def save_chat(id):
    global CHAT_ID; CHAT_ID = id
    try: open(CHAT_ID_FILE, "w").write(str(id))
    except: pass

# --- SCHEDINA 1.70 ---
async def genera_schedina(app):
    logger.info("Genero schedina 1.70")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        fixtures = api_call("fixtures", {"date": today})
        picks = []
        quota_tot = 1.0

        for f in fixtures:
            if len(picks) >= 5: break
            fid = f["fixture"]["id"]
            league = f["league"]["name"]
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]

            # Prendo le quote
            odds_data = api_call("odds", {"fixture": fid})
            if not odds_data: continue
            try:
                # Cerca 1X2 quota bassa 1.15-1.30 o Under 2.5 1.40-1.60
                for book in odds_data[0].get("bookmakers", []):
                    for bet in book.get("bets", []):
                        if bet["name"] == "Match Winner":
                            for val in bet["values"]:
                                q = float(val["odd"])
                                if 1.12 <= q <= 1.35 and quota_tot < 1.75:
                                    picks.append(f"• {home} vs {away} -> {val['value']} @ {q} ({league})")
                                    quota_tot *= q
                        if quota_tot >= 1.70: break
                    if quota_tot >= 1.70: break
            except: continue

        if len(picks) >= 3:
            txt = f"☀️ **SCHEDINA DEL GIORNO - QUOTA {quota_tot:.2f}**\n📅 {today}\n\n"
            txt += "\n".join(picks[:5])
            txt += f"\n\n💰 **Quota Tot: {quota_tot:.2f}**\n🎯 Obiettivo 1.70 con {len(picks)} partite\n\nBuona fortuna Dami!"
            await send(app, txt)
        else:
            await send(app, f"☀️ Schedina {today}: poche quote basse oggi, ti aggiorno più tardi!")
    except Exception as e:
        logger.error(f"Schedina err: {e}")

async def schedina_loop(app):
    sent_today = ""
    while True:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        # Invia alle 8:00 di mattina
        if now.hour == 8 and now.minute < 5 and sent_today!= today_str:
            if CHAT_ID:
                await genera_schedina(app)
                sent_today = today_str
        await asyncio.sleep(60)

# --- LIVE 90 SEC ---
async def live_loop(app):
    logger.info("LOOP MONDIALE 90sec PARTITO")
    while True:
        try:
            if not API_KEY: await asyncio.sleep(90); continue
            lives = api_call("fixtures", {"live": "all"})
            logger.info(f"Live: {len(lives)}")
            for m in lives:
                fid = m.get("fixture",{}).get("id")
                minute = m.get("fixture",{}).get("status",{}).get("elapsed") or 0
                if not fid or minute == 0: continue
                league = m.get("league",{}); teams = m.get("teams",{}); goals = m.get("goals",{})
                events = api_call("fixtures/events", {"fixture": fid})
                stats = api_call("fixtures/statistics", {"fixture": fid})
                shots = 0
                if stats:
                    for ts in stats:
                        for s in ts.get("statistics",[]):
                            if "Shots on Goal" in s.get("type",""): shots += int(s.get("value") or 0)
                for ev in events:
                    if ev.get("type") == "Card" and "red" in str(ev.get("detail","")).lower():
                        if ev.get("time",{}).get("elapsed",100) < 70 and fid not in ALERTED_RED:
                            ALERTED_RED.add(fid)
                            await send(app, f"🟥 **ROSSO PRIMA 70°!**\n🏆 {league.get('name')}\n⚽️ {teams.get('home',{}).get('name')} vs {teams.get('away',{}).get('name')}\n⏱️ {ev.get('time',{}).get('elapsed')}°")
                if minute <= 60 and shots >= 6 and fid not in ALERTED_HOT:
                    ALERTED_HOT.add(fid)
                    await send(app, f"🔥 **CALDA! 6 tiri entro 60°**\n🏆 {league.get('name')}\n⚽️ {teams.get('home',{}).get('name')} {goals.get('home',0)}-{goals.get('away',0)} {teams.get('away',{}).get('name')}\n⏱️ {minute}° Tiri:{shots}")
                if 60 <= minute <= 65 and shots <= 3 and fid not in ALERTED_DEAD:
                    tot = (goals.get('home') or 0)+(goals.get('away') or 0)
                    if tot <=1:
                        ALERTED_DEAD.add(fid)
                        await send(app, f"💀 **MORTA -> UNDER 2.5**\n🏆 {league.get('name')}\n⚽️ {teams.get('home',{}).get('name')} {goals.get('home')}-{goals.get('away')} {teams.get('away',{}).get('name')} | Tiri:{shots}")
        except Exception as e: logger.error(f"Live loop: {e}")
        await asyncio.sleep(90)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat(update.effective_chat.id)
    await update.message.reply_text("✅ BOT LIVE ATTIVO DAMI!\n🌍 Tutti campionati | ⏱️ 90sec | 🟥 Rosso <70 | 🔥 Calda | 💀 Morta\n☀️ Schedina 1.70 ogni mattina alle 8:00\n\nScrivi /schedina per averla subito!", parse_mode='Markdown')

async def schedina_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat(update.effective_chat.id)
    await update.message.reply_text("Genero la schedina di oggi... ⏳")
    await genera_schedina(context.application)

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN MANCANTE SU RENDER!")
        while True: time.sleep(60)
    print("BOT DAMI LIVE + SCHEDINA AVVIATO")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedina", schedina_cmd))
    async def startup(a):
        asyncio.create_task(live_loop(a))
        asyncio.create_task(schedina_loop(a))
    app.post_init = startup
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
