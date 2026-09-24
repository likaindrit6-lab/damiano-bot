import os, time, requests
TOKEN = os.getenv("TELEGRAM_TOKEN","").strip()
CHAT = os.getenv("CHAT_ID","").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
print(f"AVVIO TOKEN={TOKEN[:10]} CHAT={CHAT}", flush=True)
def send(t):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=15)
        print(f"SEND -> {r.status_code} | {r.text[:300]}", flush=True)
    except Exception as e:
        print(f"ERR {e}", flush=True)

send("✅ BOT PARTITO Dami - questo è il test")
while True:
    try:
        h={"x-apisports-key": API}
        j=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=h, timeout=20).json()
        print(f"live: {len(j.get('response',[]))} partite", flush=True)
    except Exception as e:
        print(f"loop {e}", flush=True)
    time.sleep(60)
