import os
import time
import requests
from datetime import datetime
import pytz

API_KEY = os.getenv("API_KEY") # usa la stessa chiave che hai già per il calcio
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TZ_ITALY = pytz.timezone("Europe/Rome")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})

def get_today_games():
    today = datetime.now(TZ_ITALY).strftime("%Y-%m-%d")
    url = "https://v1.basketball.api-sports.io/games"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, params={"date": today}, timeout=20)
    return r.json().get("response", [])

def get_odds(game_id):
    url = "https://v1.basketball.api-sports.io/odds"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, params={"game": game_id}, timeout=20)
    return r.json().get("response", [])

# Loop che aspetta le 8 di mattina ora italiana
already_sent_today = None

while True:
    now_italy = datetime.now(TZ_ITALY)
    today_str = now_italy.strftime("%Y-%m-%d")

    # Se sono le 8 di mattina e non ho già inviato oggi
    if now_italy.hour == 8 and now_italy.minute == 0 and already_sent_today != today_str:
        print(f"[{now_italy}] Sono le 8, faccio la chiamata giornaliera")
        try:
            games = get_today_games()
            report = f"🏀 *BASKET OGGI {today_str} - Handicap 12+*\nTotale partite oggi: {len(games)}\n\n"
            found = 0

            for g in games:
                game_id = g["id"]
                odds_data = get_odds(game_id)
                
                for odd in odds_data:
                    for book in odd.get("bookmakers", [])[:2]: # guardo solo primi 2 bookmaker per non consumare
                        for bet in book.get("bets", []):
                            # Handicap basket di solito id 8 o 32
                            if "handicap" in bet["name"].lower() or bet["id"] in [8, 32, 4]:
                                for val in bet.get("values", []):
                                    try:
                                        # val['value'] tipo "Home +12.5"
                                        raw = val.get("value", "") + " " + val.get("handicap", "")
                                        # prendo il numero
                                        import re
                                        m = re.search(r'([+-]?\d+\.?\d*)', raw)
                                        if m:
                                            num = abs(float(m.group(1)))
                                            if num >= 12:
                                                home = g["teams"]["home"]["name"]
                                                away = g["teams"]["away"]["name"]
                                                ora = datetime.fromisoformat(g["date"].replace("Z","+00:00")).astimezone(TZ_ITALY).strftime("%H:%M")
                                                report += f"• {ora} - {home} vs {away}\n  {val['value']} (H: {num}) Quota {val.get('odd','-')}\n\n"
                                                found += 1
                                                raise StopIteration # esco per questa partita, ne ho trovata una
                                    except StopIteration:
                                        break
                                    except:
                                        continue

            if found == 0:
                report += "Nessuna partita con handicap 12+ trovata oggi."

            send_telegram(report)
            already_sent_today = today_str
            print("Report inviato")

        except Exception as e:
            print(f"Errore: {e}")
            send_telegram(f"Errore bot basket: {e}")
            already_sent_today = today_str # per non riprovare all'infinito

    time.sleep(50) # controlla ogni 50 secondi
