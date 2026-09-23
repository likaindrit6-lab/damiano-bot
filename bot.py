
import os, time, requests
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

print("--- BOT AVVIATO ---")
send("✅ <b>Bot Damiano CONNESSO!</b>\nSe leggi questo, il bot funziona. Ora controllo le live ogni 60 sec.")

while True:
    try:
        now = datetime.now(pytz.timezone("Europe/Rome"))
        print(f"[{now.strftime('%H:%M:%S')}] Controllo live...")
        
        # Test chiamata API
        headers = {"x-apisports-key": API_KEY}
        r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=10)
        data = r.json()
        live_count = len(data.get("response", []))
        
        print(f"Trovate {live_count} partite live")
        
        time.sleep(60)
    except Exception as e:
        print(f"ERRORE: {e}")
        time.sleep(30)
