import os, time, requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

TOP_ONLY = False # False = TUTTO IL MONDO DENTRO
TOP_LEAGUES = [135,39,140,78,61,2,3] # Serie A, Premier, Liga, Bundesliga, Ligue1, UCL, UEL

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass

def get_live():
    # FIX DEFINITIVA
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, timeout=20).json()
    # logga se c'è errore API
    if "errors" in r and r["errors"]:
        print(f"ERRORE API: {r['errors']}")
    return r.get("response", [])

print("BOT PARTITO - TOP_ONLY=False - TUTTO IL MONDO")
tg("✅ Bot riavviato - adesso cerco in tutto il mondo")

while True:
    try:
        games = get_live()
        print(f"VISTO {len(games)} live") # solo log, non telegram

        for g in games:
            if TOP_ONLY and g["league"]["id"] not in TOP_LEAGUES:
                continue
            
            minute = g["fixture"]["status"]["elapsed"] or 0
            if minute < 10 or minute > 75: # solo 10-75 come volevi tu
                continue
            
            # percentuale semplice
            perc = 50
            if g["goals"]["home"] == 0 and g["goals"]["away"] == 0:
                perc = 70
            elif abs(g["goals"]["home"] - g["goals"]["away"]) == 1:
                perc = 75

            if perc >= 65:
                txt = f"🔥 {minute}' {g['league']['country']} {g['league']['name']}\n{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\nPercentuale gol: {perc}%"
                tg(txt)
                print(f"INVIATO: {txt}")

    except Exception as e:
        print(f"ERRORE LOOP: {e}")

    time.sleep(180) # 3 min
