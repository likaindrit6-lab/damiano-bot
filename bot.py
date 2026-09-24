import os, time, requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")
API = os.getenv("API_FOOTBALL_KEY")

print("AVVIO", flush=True)

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT, "text": t}, timeout=10)
        print(f"inviato: {t}", flush=True)
    except Exception as e:
        print(f"errore invio: {e}", flush=True)

send("✅ BOT PARTITO Dami - se leggi questo Telegram è ok")

h = {"x-apisports-key": API}

while True:
    try:
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=h, timeout=20).json().get("response",[])
        print(f"live: {len(live)} partite", flush=True)
        time.sleep(60)
    except Exception as e:
        print(f"errore loop: {e}", flush=True)
        time.sleep(30)
