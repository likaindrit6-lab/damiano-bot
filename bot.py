
import os, requests, time
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
        print(f"Inviato: {text[:50]}")
    except Exception as e:
        print(f"Errore invio: {e}")

send("Bot riavviato correttamente ✅ Ora non spamma più, gira 1 volta sola.")

# loop che tiene il bot acceso senza farlo crashare
while True:
    now = datetime.now().strftime("%H:%M:%S")
    print(f"Bot vivo - {now}")
    time.sleep(60) # aspetta 1 minuto e ricontrolla, non si spegne più
