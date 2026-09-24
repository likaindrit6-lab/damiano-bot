
import requests
import time

TELEGRAM_TOKEN = "METTI_QUI_IL_TUO_TOKEN"
CHAT_ID = "METTI_QUI_IL_TUO_CHAT_ID"

print(">>> STO PARTENDO DAMI <<<")

def tg(msg):
    print(f">>> Provo a mandare: {msg}")
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": msg})
    print(f">>> Risposta Telegram: {r.text}")

tg("✅ PROVA DAMI - Se leggi questo, bot.py funziona")

while True:
    print("Bot vivo... aspetto 60 sec")
    time.sleep(60)
