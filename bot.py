
import os, requests, time
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
print("TEST TELEGRAM IN CORSO...")
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
r = requests.post(url, data={"chat_id": CHAT_ID, "text": "🔥 TEST OK - Se leggi questo, Telegram funziona - Dami"}, timeout=15)
print(f"Risposta Telegram: {r.text}")
while True:
    print("Bot vivo...")
    time.sleep(60)
