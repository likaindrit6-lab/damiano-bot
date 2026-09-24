import os, requests
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")
print(f"TOKEN? {bool(TOKEN)} CHAT? {bool(CHAT)}")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
r = requests.post(url, data={"chat_id": CHAT, "text": "✅ TEST - se leggi questo, Telegram funziona"})
print(r.text)
