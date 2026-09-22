
import os, requests
from telegram.ext import ApplicationBuilder, ContextTypes

CHAT_ID = os.getenv("CHAT_ID")
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

def get_stats(fixture_id):
    try:
        headers = {"x-apisports-key": FOOTBALL_API_KEY}
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}", headers=headers, timeout=20)
        data = r.json().get("response", [])
        if not data:
            return 0, 0
        shots_on = 0
        for team_stat in data:
            for s in team_stat.get("statistics", []):
                if s["type"] == "Shots on Goal":
                    shots_on += s["value"] or 0
        return shots_on, 0
    except:
        return 0, 0

async def check_all(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID or not FOOTBALL_API_KEY:
        return
    for m in get_live():
        try:
            fid = m["fixture"]["id"]
            minute = m["fixture"]["status"]["elapsed"] or 0
            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]
            score = f"{m['goals']['home'] or 0}-{m['goals']['away'] or 0}"
            shots_on, _ = get_stats(fid)

            # 1. CALDA
            if shots_on >= 6 and fid not in alerted_calda:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"🔥 CALDA {minute}' {home} vs {away} {score} - {shots_on} tiri in porta - PUNTA")
                alerted_calda.add(fid)
                bet_attive.add(fid)
                last_scores[fid] = score

            # 2. MORTA
            if 44 <= minute <= 48 and shots_on <= 3 and fid not in alerted_morta and fid not in alerted_calda:
                await context.bot.send_message(chat_id=CHAT_ID, text=f"💀 MORTA HT {home} vs {away} {score} - solo {shots_on} tiri in porta")
                alerted_morta.add(fid)

            # 3. GOAL solo se calda
            if fid in bet_attive:
                old = last_scores.get(fid)
                if old and old!= score:
                    await context.bot.send_message(chat_id=CHAT_ID, text=f"⚽ GOAL! {home} vs {away} ora {score} - VINTA")
                    bet_attive.remove(fid)
                last_scores[fid] = score
        except Exception as e:
            print(f"Errore su {fid}: {e}")
            continue
