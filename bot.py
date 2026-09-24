import os, time, requests

TOKEN = os.getenv("TELEGRAM_TOKEN","").strip()
CHAT = os.getenv("CHAT_ID","").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()

print(f"AVVIO TOKEN={TOKEN[:10]}... CHAT={CHAT}", flush=True)

def send(t):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT, "text": t}, timeout=15)
        print(f"SEND -> {r.status_code} | {r.text[:300]}", flush=True)
        return r.status_code == 200
    except Exception as e:
        print(f"ERR SEND {e}", flush=True)
        return False

if not send("✅ BOT PARTITO Dami - se leggi questo è TUTTO OK"):
    print("TELEGRAM FALLITO - Controlla TOKEN e CHAT_ID", flush=True)

h = {"x-apisports-key": API}
while True:
    try:
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=h, timeout=20).json().get("response",[])
        print(f"live: {len(live)} partite", flush=True)
        time.sleep(60)
    except Exception as e:
        print(f"loop err {e}", flush=True)
        time.sleep(30)
