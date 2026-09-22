import os
import asyncio
import requests
from datetime import datetime, time
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import NetworkError, Conflict

CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

# Memorie
alerted_calda = set()
alerted_morta = set()
alerted_corner = set()
alerted_sblocco = set()
bet_attive = set()
last_scores = {}

def api_get(url):
    headers = {"x-apisports-key": FOOTBALL_API_KEY}
    r = requests.get(url, headers=headers, timeout=25)
    return r.json()

def get_live():
    data = api_get("https://v3.football.api-sports.io/fixtures?live=all")
    return data.get("response", [])

def get_stats_completo(fid):
    try:
        data = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
        shots = 0
        corners = 0
        for team in data.get("response", []):
            for s in team.get("statistics", []):
                if s["type"] == "Shots on Goal":
                    shots += int(s["value"] or 0)
                if s["type"] == "Corner Kicks":
                    corners += int(s["value"] or 0)
        return shots, corners
    except:
        return 0, 0

def get_today_fixtures():
    today = datetime.now().strftime("%Y-%m-%d")
    data = api_get(f"https://v3.football.api-sports.io/fixtures?date={today}")
    return data.get("response", [])

def get_last_5_avg(team_id):
    try:
        data = api_get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5")
        fixtures = data.get("response", [])
        if len(fixtures) < 3: return 0
        total = 0
        for f in fixtures:
            total += (f["goals"]["home"] or 0) + (f["goals"]["away"] or 0)
        return total / len(fixtures)
    except:
        return 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 DAMI BOT OK! Attivo 09:00-01:00 ogni 2 min - 09:00 PRE-CALDE - Parte subito!")

async def schedina_mattutina(context):
    try:
        await context.bot.send_message(chat_id=CHAT_ID, text="☀️ BUONGIORNO DAMI! Analizzo partite OGGI sopra 2.8 gol media ultime 5...")
        fixtures = get_today_fixtures()
        pre_calde = []
        for m in fixtures[:100]:
            try:
                home_id = m["teams"]["home"]["id"]
                away_id = m["teams"]["away"]["id"]
                home_name = m["teams"]["home"]["name"]
                away_name = m["teams"]["away"]["name"]
                orario = m["fixture"]["date"][11:16]
                avg_h = get_last_5_avg(home_id)
                avg_a = get_last_5_avg(away_id)
                avg_tot = (avg_h + avg_a) / 2
                if avg_tot >= 2.8:
                    pre_calde.append(f"🔥 {orario} {home_name} vs {away_name} - {avg_tot:.1f} gol media")
                await asyncio.sleep(0.4)
            except: continue

        if pre_calde:
            msg = f"🔥 PRE-CALDE OGGI sopra 2.8 ({len(pre_calde)} partite):\n\n" + "\n".join(pre_calde[:30]) + "\n\nPunta Over 1.5 / 2.5"
        else:
            msg = "Oggi nessuna sopra 2.8 media. Giornata calma."
        await context.bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"Errore schedina: {e}")

async def check_all(context):
    # PAUSA NOTTE 01:00-09:00 COME HAI CHIESTO TU
    tz = pytz.timezone("Europe/Rome")
    now_hour = datetime.now(tz).hour
    if 1 <= now_hour < 9:
        print(f"Zzz pausa notte {now_hour}:00 - 0 token")
        return

    try:
        live = get_live()
        print(f"Live trovate: {len(live)}")
    except: return

    for m in live:
        try:
            fid = m["fixture"]["id"]
            minute = m["fixture"]["status"]["elapsed"] or 0
            if minute < 10 or minute > 88: continue

            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]
            score = f"{m['goals']['home'] or 0}-{m['goals']['away'] or 0}"

            # Se già CALDA, controllo solo GOAL per risparmiare token
            if fid in alerted_calda:
                old = last_scores.get(fid)
                if old and old!= score:
                    await context.bot.send_message(chat_id=CHAT_ID, text=f"⚽ GOAL! {home} vs {away} ora {score} - VINTA 🔥")
                    bet_attive.discard(fid)
                last_scores[fid] = score
                continue

            shots, corners = get_stats_completo(fid)

            # 1. CALDA 6 tiri
            if shots >= 6 and fid not in alerted_calda:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"🔥 CALDA {minute}' {home} vs {away} {score} - {shots} tiri - PUNTA GOL")
                alerted_calda.add(fid)
                bet_attive.add(fid)
                last_scores[fid] = score

            # 2. MORTA HT
            if 44 <= minute <= 48 and shots <= 3 and fid not in alerted_morta:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"💀 MORTA HT {home} vs {away} {score} - solo {shots} tiri")
                alerted_morta.add(fid)

            # 3. SBLOCCO 70' con 5 tiri totali come vuoi tu
            if 70 <= minute <= 80 and score in ["0-0","1-0","0-1","1-1"] and fid not in alerted_sblocco:
                if shots >= 5:
                    await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 SBLOCCO {minute}' {home} vs {away} {score} - {shots} tiri - SI SBLOCCA ORA!")
                    alerted_sblocco.add(fid)

            # 4. CORNER 8 corner al 60'
            if 60 <= minute <= 80 and corners >= 8 and fid not in alerted_corner:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"🚩 CORNER CALDO {minute}' {home} vs {away} {score} - {corners} corner - PUNTA OVER CORNER")
                alerted_corner.add(fid)

        except Exception as e:
            print(f"Errore: {e}")
            continue

async def error_handler(update, context):
    print(f"ERRORE: {context.error}")
    await asyncio.sleep(10)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_error_handler(error_handler)
    app.job_queue.run_repeating(check_all, interval=120, first=10) # OGNI 2 MINUTI
    tz = pytz.timezone("Europe/Rome")
    app.job_queue.run_daily(schedina_mattutina, time=time(hour=9, minute=0, tzinfo=tz), name="schedina_9")
    print("Bot DAMI avviato - TUTTO ATTIVO")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False, stop_signals=None)
