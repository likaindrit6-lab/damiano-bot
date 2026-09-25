import os, time, requests
print("--- BOT USO I TUOI NOMI ORIGINALI ---", flush=True)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=15)
    except Exception as e:
        print(f"ERRORE TG: {e}", flush=True)

tg("✅ OK Dami, ora uso TELEGRAM_TOKEN come l'hai chiamato tu. Scusa per prima.")
