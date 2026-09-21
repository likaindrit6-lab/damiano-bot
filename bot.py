
import os, time, threading, requests, datetime
from flask import Flask

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
CHAT_ID = None

app = Flask(__name__)
@app.route('/')
def home(): 
    return f"DAMI V7.1 FIX - RUNNING - Chat: {CHAT_ID} - Key: {'OK' if API_KEY else 'MANCANTE'}"

def send_tg(text):
    global CHAT_ID
    if not CHAT_ID or not TELEGRAM_TOKEN:
        print("NO CHAT_ID o TOKEN")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
        print(f"INVIATO TG: {text[:50]}")
    except Exception as e:
        print(f"Err send_tg {e}")

def api_get(url):
    try:
        h = {"x-apisports-key": API_KEY}
        r = requests.get(url, headers=h, timeout=20)
        print(f"API {r.status_code} - {url[-30:]}")
        return r.json()
    except Exception as e:
        print(f"Err api_get {e}")
        return {"response":[]}

def get_updates():
    global CHAT_ID
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?timeout=30&offset={offset}"
            r = requests.get(url, timeout=35).json()
            for upd in r.get("result",[]):
                offset = upd["update_id"]+1
                if "message" in upd:
                    txt = upd["message"].get("text","")
                    cid = upd["message"]["chat"]["id"]
                    if "/start" in txt:
                        CHAT_ID = cid
                        send_tg(f"🔥 V7.1 FIX ATTIVO!\nChat salvata: {cid}\n90 sec x 10 partite\n\nDentro:\n⚠️ 0.5 PRIMA\n🔥 CALDA 6 tiri\n💀 MORTA\n🟥 ROSSO\n🎟️ SCHEDINA 10:00")
        except Exception as e:
            print(f"Err getUpdates {e}")
            time.sleep(5)

def loop_bot():
    memoria = {}
    chiamate = 0
    schedina_fatta = None
    while True:
        try:
            now = datetime.datetime.now()
            if chiamate > 7000:
                print("7000 raggiunte dormo 1h")
                time.sleep(3600)
                chiamate = 0

            # SCHEDINA 10:00
            if now.hour == 10 and now.minute < 10 and schedina_fatta != now.date():
                schedina_fatta = now.date()
                send_tg("🎟️ SCHEDINA 10:00 in preparazione...")

            data = api_get("https://v3.football.api-sports.io/fixtures?live=all")
            lives = data.get("response", [])
            chiamate += 1

            lives_00 = [f for f in lives if f["goals"]["home"]==0 and f["goals"]["away"]==0]
            lives_00 = sorted(lives_00, key=lambda x: x["fixture"]["status"]["elapsed"] or 0, reverse=True)[:10]

            print(f"LIVE 0-0: {len(lives_00)
