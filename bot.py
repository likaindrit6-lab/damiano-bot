
from flask import Flask
import threading, time, requests, os

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
HEADERS = {"x-apisports-key": API_KEY}

print(f"CHECK ENV: API_KEY={'OK' if API_KEY else 'MANCANTE'} BOT_TOKEN={'OK' if BOT_TOKEN else 'MANCANTE'} CHAT_ID={CHAT_ID}", flush=True)

# Sblocca telegram all'avvio
if BOT_TOKEN:
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook").json()
        print(f"DELETE WEBHOOK: {r}", flush=True)
    except Exception as e:
        print(f"ERRORE WEBHOOK: {e}", flush=True)

partite_calde = {}
offset = 0

def manda(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
    except Exception as e:
        print(f"ERRORE MANDA: {e}", flush=True)

def handle_commands():
    global offset
    print("HANDLE COMMANDS PARTITO", flush=True)
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=20").json()
            if not resp.get('ok'):
                print(f"ERRORE TELEGRAM getUpdates: {resp}", flush=True)
                time.sleep(5)
                continue
            for upd in resp.get('result',[]):
                offset = upd['update_id']+1
                txt = upd.get('message',{}).get('text','')
                cid = upd.get('message',{}).get('chat',{}).get('id')
                print(f"COMANDO RICEVUTO: {txt} da {cid}", flush=True)
                if '/start' in txt:
                    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={cid}&text=✅ V42 SBLOCCATO! CHAT: {cid}")
        except Exception as e:
            print(f"ERRORE handle: {e}", flush=True)
        time.sleep(2)

def loop_bot():
    print("LOOP BOT PARTITO", flush=True)
    while True:
        try:
            if not API_KEY:
                print("API_KEY MANCANTE SU RENDER!", flush=True)
                time.sleep(10)
                continue
            live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS).json()
            print(f"Live trovate: {len(live.get('response',[]))}", flush=True)
        except Exception as e:
            print(f"ERRORE LOOP: {e}", flush=True)
        time.sleep(90)

@app.route("/")
def home(): return "V42 DEBUG OK"

threading.Thread(target=loop_bot, daemon=True).start()
threading.Thread(target=handle_commands, daemon=True).start()
