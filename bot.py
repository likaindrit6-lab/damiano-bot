import os
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TZ_ITALY = ZoneInfo("Europe/Rome")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})

def get_today_games():
    today = datetime.now(TZ_ITALY).strftime("%Y-%m-%d")
    url = "https://v1.basketball.api-sports.io/games"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, params={"date": today})
    print(f"Status games: {r.status_code}")
    return r.json().get("response", [])

def get_odds(game_id):
    url = "https://v1.basketball.api-sports.io/odds"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, params={"game": game_id})
    return r.json().get("response", [])

already_sent_today = None

print("Bot basket partito - aspetta le 8:00")

while True:
    now_italy = datetime.now(TZ_ITALY)
    today_str = now_italy.strftime("%Y-%m-%d")

    if now_italy.hour == 8 and now_italy.minute == 0 and already_sent_today != today_str:
        try:
            games = get_today_games()
            report = f"BASKET OGGI {today_str} - Handicap 12+\nTotale partite: {len(games)}\n\n"
            found = 0

            for g in games:
                odds_data = get_odds(g["id"])
                for odd in odds_data:
                    for book in odd.get("bookmakers", [])[:1]:
                        for bet in book.get("bets", []):
                            if "handicap" in bet["name"].lower():
                                for val in bet.get("values", []):
                                    try:
                                        raw = val.get("value", "")
                                        # prende l'ultimo numero tipo +12.5
                                        import re
                                        m = re.search(r'([+-]?\d+\.?\d*)', raw)
                                        if m:
                                            num = abs(float(m.group(1)))
                                            if num >= 12:
                                                home = g["teams"]["home"]["name"]
                                                away = g["teams"]["away"]["name"]
                                                ora = datetime.fromisoformat(g["date"].replace("Z","+00:00")).astimezone(TZ_ITALY).strftime("%H:%M")
                                                report += f"{ora} - {home} vs {away} -> {val['value']} quota {val.get('odd','-')}\n"
                                                found += 1
                                                break
                                    except:
                                        continue

            if found == 0:
                report += "Nessuna partita con handicap 12+ oggi."

            send_telegram(report)
            already_sent_today = today_str
            print("Report inviato")
            
        except Exception as e:
            print(f"Errore: {e}")
            already_sent_today = today_str

    time.sleep(50)
