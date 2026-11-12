import logging
import os
import re
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
from flask import Flask

API_KEY = os.environ.get("API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_BASE = "https://v1.basketball.api-sports.io"
ROME = ZoneInfo("Europe/Rome")
RUN_HOUR = 8
HANDICAP_MIN = 12

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("basket-bot")

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot basket live - OK. Vai su /test per provare"

@app.route("/test")
def test():
    send_telegram("✅ Test bot riuscito! Collegamento OK.")
    return "Test inviato su Telegram!"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=30)
    response.raise_for_status()

# ... tutto il resto uguale al tuo ...
def fetch_games(date_str):
    response = requests.get(f"{API_BASE}/games", params={"date": date_str}, headers={"x-apisports-key": API_KEY}, timeout=30)
    response.raise_for_status()
    return response.json().get("response", [])

def fetch_odds(game_id):
    response = requests.get(f"{API_BASE}/odds", params={"game": game_id}, headers={"x-apisports-key": API_KEY}, timeout=30)
    response.raise_for_status()
    return response.json().get("response", [])

def parse_line(value_label):
    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", value_label or "")
    return float(numbers[-1]) if numbers else None

def handicap_12_plus_outcomes(odds_items):
    best = {}
    for item in odds_items:
        for bookmaker in item.get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                if "handicap" not in (bet.get("name") or "").lower():
                    continue
                for value in bet.get("values", []):
                    label = value.get("value") or ""
                    line = parse_line(label)
                    if line is None or abs(line) < HANDICAP_MIN:
                        continue
                    try:
                        odd = float(value.get("odd"))
                    except (TypeError, ValueError):
                        continue
                    if label not in best or odd > best[label]:
                        best[label] = odd
    return best

def format_game_time(iso_date):
    parsed = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    return parsed.astimezone(ROME).strftime("%H:%M")

def run_daily_check():
    today = datetime.now(ROME).strftime("%Y-%m-%d")
    games = fetch_games(today)
    messages = []
    for game in games:
        home = game.get("teams", {}).get("home", {}).get("name", "?")
        away = game.get("teams", {}).get("away", {}).get("name", "?")
        game_time = format_game_time(game.get("date", ""))
        outcomes = handicap_12_plus_outcomes(fetch_odds(game["id"]))
        for odd in outcomes.values():
            messages.append(f"🏀 HANDICAP 12+ - OGGI - {home} vs {away} - Ore {game_time} - Quota: {odd}")
    if not messages:
        send_telegram("Oggi nessuna partita con handicap 12+")
        return
    for message in messages:
        send_telegram(message)

def seconds_until_next_run(now):
    target = now.replace(hour=RUN_HOUR, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()

def scheduler_loop():
    while True:
        try:
            wait = seconds_until_next_run(datetime.now(ROME))
            log.info("Prossima esecuzione tra %.0f secondi", wait)
            time.sleep(wait)
            run_daily_check()
        except Exception:
            log.exception("Errore nel controllo giornaliero")
            time.sleep(60)

def start_scheduler():
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

if __name__ == "__main__":
    start_scheduler()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
