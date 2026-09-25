import os, time, requests
from datetime import datetime

# --- CONFIG CHE CAMBI TU ---
TOP_ONLY = False  # False adesso = TUTTO IL MONDO, True dopo = solo top
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

TOP_LEAGUES = [135, 39, 140, 78, 61, 2, 3] # Serie A, Premier, Liga, Bundesliga, Ligue1, Champions, etc.

def send_telegram(text):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def get_live():
    # QUESTA E' LA FIX - live=all invece di date
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, timeout=20).json()
    return r.get("response", [])

def calc_percentuale(fixture):
    # la tua percentuale gol come volevi tu
    stats = fixture.get("statistics", []) # qui poi leggi angoli/tiri
    perc = 50
    # logica semplice per ora - poi la miglioriamo con angoli
    if fixture["goals"]["home"] == 0 and fixture["goals"]["away"] == 0:
        perc += 15 # 0-0 caldo
    if fixture["fixture"]["status"]["elapsed"] >= 30:
        perc += 15
    # se tanti angoli +20 ecc
    return min(perc, 92)

# LOOP PRINCIPALE - OGNI 3 MINUTI, NON OGNI MINUTO
while True:
    try:
        live_games = get_live()
        print(f"VISTO {len(live_games)} partite live") # solo nei log, non su Telegram!

        for game in live_games:
            league_id = game["league"]["id"]
            if TOP_ONLY and league_id not in TOP_LEAGUES:
                continue

            minute = game["fixture"]["status"]["elapsed"] or 0
            if minute > 75: # dopo 75' basta come mi hai detto
                continue

            perc = calc_percentuale(game)
            if perc >= 65: # solo se caldo 65-70%
                country = game["league"]["country"]
                league = game["league"]["name"]
                home = game["teams"]["home"]["name"]
                away = game["teams"]["away"]["name"]
                score = f"{game['goals']['home']}-{game['goals']['away']}"
                
                msg = f"🔥 {minute}' - {country} {league}\n{home} {score} {away}\nPercentuale gol: {perc}% - sta spingendo"
                send_telegram(msg)

    except Exception as e:
        print(f"ERRORE {e}")

    time.sleep(180) # 3 minuti, così non finisci le 7200 chiamate
