import os, time, requests
from datetime import datetime
print("--- BOT COMPLETO CARICATO ---", flush=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

TOP_ONLY = False  # False = TUTTO IL MONDO, True = solo top quando iniziano campionati
TOP_LEAGUES = [135,39,140,78,61,2,3,848] # Serie A, Premier, Liga, Bundes, Ligue1, UCL, UEL, Euro

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print(f"INVIATO TG: {msg[:60]}", flush=True)
    except Exception as e:
        print(f"ERRORE TG: {e}", flush=True)

def get_live():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, timeout=20).json()
    if "errors" in r and r["errors"]:
        print(f"ERRORE API: {r['errors']}", flush=True)
        # se rate limit o chiave scaduta lo vedi qui
    return r.get("response", [])

def calc_percentuale(game):
    minute = game["fixture"]["status"]["elapsed"] or 0
    home_goals = game["goals"]["home"] or 0
    away_goals = game["goals"]["away"] or 0
    
    perc = 50
    # 0-0 caldo
    if home_goals == 0 and away_goals == 0:
        perc += 20
        if minute >= 30: perc += 10
        if minute >= 60: perc += 10
    # 1-0 / 0-1 partita aperta per pareggio
    elif abs(home_goals - away_goals) == 1:
        perc += 25
    # tanti gol già fatti = altro gol
    elif home_goals + away_goals >= 2:
        perc += 10

    if minute >= 70:
        perc -= 15 # dopo 70 cala un po'

    return min(max(perc, 40), 92)

tg("✅ BOT COMPLETO ATTIVO - TUTTO IL MONDO - con percentuale gol fino al 75'")

while True:
    try:
        games = get_live()
        print(f"{datetime.now().strftime('%H:%M:%S')} - VISTO {len(games)} live", flush=True)

        for g in games:
            try:
                league_id = g["league"]["id"]
                if TOP_ONLY and league_id not in TOP_LEAGUES:
                    continue

                minute = g["fixture"]["status"]["elapsed"] or 0
                if minute < 10 or minute > 75:
                    continue

                perc = calc_percentuale(g)

                if perc >= 65: # solo se caldo come volevi tu
                    country = g["league"]["country"]
                    league = g["league"]["name"]
                    home = g["teams"]["home"]["name"]
                    away = g["teams"]["away"]["name"]
                    score = f"{g['goals']['home']}-{g['goals']['away']}"

                    # anti-spam: manda solo 1 volta per partita ogni 15 min
                    msg = f"🔥 <b>{minute}' - {country} {league}</b>\n{home} {score} {away}\n<b>Percentuale gol: {perc}%</b> - sta spingendo!"
                    tg(msg)
                    time.sleep(2) # pausa tra messaggi

            except Exception as e:
                print(f"ERRORE partita: {e}", flush=True)
                continue

    except Exception as e:
        print(f"ERRORE LOOP: {e}", flush=True)

    time.sleep(180) # 3 minuti, non consuma le 7200 chiamate
