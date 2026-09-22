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

last_scores={}; alerted_red=set(); alerted_calda=set(); alerted_morta=set()

def get_live():
    try:
        r=requests.get(f"{API_URL}/fixtures?live=all", headers=HEADERS, timeout=15)
        return r.json().get("response", [])
    except: return []

def get_stats(fid):
    try:
        r=requests.get(f"{API_URL}/fixtures/statistics?fixture={fid}", headers=HEADERS, timeout=10).json().get("response", [])
        shots_on=0; corners=0
        for team in r:
            for s in team.get("statistics", []):
                if s["type"]=="Shots on Goal": shots_on+= s["value"] or 0
                if s["type"]=="Corner Kicks": corners+= s["value"] or 0
        return shots_on, corners
    except: return 0,0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔥 DAMI BOT FINALE ATTIVO!\n✅ 5-6 partite quota 1.70/1.80 alle 09:00\n✅ 🔥 CALDA 8 tiri al 70'\n✅ 💀 MORTA\n✅ 🟥 ROSSO <60' + ⚽ GOAL")

async def check_all(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID or not FOOTBALL_API_KEY: return
    for m in get_live():
        fid=m["fixture"]["id"]; minute=m["fixture"]["status"]["elapsed"] or 0
        home=m["teams"]["home"]["name"]; away=m["teams"]["away"]["name"]
        hg=m["goals"]["home"] or 0; ag=m["goals"]["away"] or 0
        score=f"{hg}-{ag}"
        if fid in last_scores and last_scores[fid]!=score:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"⚽ GOAL {minute}' {home} vs {away} -> {score}")
        last_scores[fid]=score

        if minute>=70:
            shots_on, corners = get_stats(fid)
            if shots_on>=8 and fid not in alerted_calda:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"🔥 CALDA {minute}' {home} vs {away} {score}\n{shots_on} tiri in porta, {corners} angoli - STA PER GOL!")
                alerted_calda.add(fid)
            if score=="0-0" and shots_on<=2 and fid not in alerted_morta:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"💀 MORTA {minute}' {home} vs {away} 0-0\nSolo {shots_on} tiri - LASCIA PERDERE")
                alerted_morta.add(fid)

        if 0<minute<60 and fid not in alerted_red:
            try:
                ev=requests.get(f"{API_URL}/fixtures/events?fixture={fid}", headers=HEADERS, timeout=10).json().get("response", [])
                for e in ev:
                    if e["type"]=="Card" and "red" in e["detail"].lower() and e["time"]["elapsed"]<60:
                        await context.bot.send_message(chat_id=CHAT_ID, text=f"🟥 ROSSO {minute}' {home} vs {away} {score} - ORA GOL!")
                        alerted_red.add(fid); break
            except: pass

async def schedina_mattutina(context: ContextTypes.DEFAULT_TYPE):
    # COSTRUISCE SCHEDINA DA 5-6 SQUADRE QUOTA 1.70-1.80
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        # Prende partite di oggi
        fixtures = requests.get(f"{API_URL}/fixtures?date={today}", headers=HEADERS, timeout=15).json().get("response", [])[:20]

        schedina = []
        quota_tot = 1.0

        # Logica: prende Over 0.5 gol (quota ~1.10) x 6 partite = ~1.77
        for f in fixtures:
            if len(schedina) >= 6: break
            fid = f["fixture"]["id"]
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            league = f["league"]["name"]
            ora = f["fixture"]["date"][11:16]

            # Cerca quota Over 0.5 (sicura)
            try:
                odds_data = requests.get(f"{API_URL}/odds?fixture={fid}", headers=HEADERS, timeout=10).json().get("response", [])
