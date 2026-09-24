import os, time, requests
TOKEN = os.getenv("TELEGRAM_TOKEN","").strip()
CHAT = os.getenv("CHAT_ID","").strip()

def send(t):
    r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=10)
    print(f"SEND {r.status_code} {r.text[:200]}")

send("✅ PROVA TELEGRAM - Se leggi questo abbiamo vinto")
while True:
    time.sleep(60)
    send("sono vivo")
