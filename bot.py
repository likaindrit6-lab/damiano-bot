
import os
import time
import requests
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def get_live_matches():
    # Qui c'è la tua logica API-Football per i live mondiali
    # Ritorna lista partite live
    return []

def analizza_partita(match):
    # Logica tua: CALDA / TIRI / ANGOLI / ROSSO / MORTA
    # Esempio:
    # if condizioni -> return "🔥 CALDA TIRI ..."
    return None

def invia_schedine_giorno():
    # La tua logica schedine delle 10:00
    send_telegram("⚽ *Schedine di oggi pronte*...")

def loop_live():
    rome = pytz.timezone("Europe/Rome")
    now = datetime.now(rome)
    
    # Attivo solo dalle 10:01 alle 23:00
    if not (10 <= now.hour < 23 or (now.hour == 10 and now.minute >= 1)):
        return

    matches = get_live_matches()
    for m in matches:
        segnale = analizza_partita(m)
        if segnale:
            send_telegram(segnale)
            time.sleep(2)

# --- MAIN ---
if __name__ == "__main__":
    rome = pytz.timezone("Europe/Rome")
    print("Bot avviato...")

    schedine_inviate_oggi = False

    while True:
        now = datetime.now(rome)

        # 10:00 Schedine
        if now.hour == 10 and now.minute == 0 and not schedine_inviate_oggi:
            try:
                invia_schedine_giorno()
                schedine_inviate_oggi = True
            except Exception as e:
                print(f"Errore schedine: {e}")

        # Reset flag dopo le 10:01
        if now.hour == 10 and now.minute == 1:
            schedine_inviate_oggi = False

        # Live ogni 90 secondi dalle 10:01 alle 23:00
        if (10 <= now.hour < 23):
            if not (now.hour == 10 and now.minute == 0):
                try:
                    loop_live()
                except Exception as e:
                    print(f"Errore live: {e}")

        time.sleep(90)
