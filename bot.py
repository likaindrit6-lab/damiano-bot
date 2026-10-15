import os, requests, threading, json, time, traceback
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT = os.getenv('BOT_TOKEN')
CHAT = os.getenv('CHAT_ID')
KEY = os.getenv('API_FOOTBALL_KEY')

print("=== ENV CHECK ===")
print(f"BOT_TOKEN: {'OK' if BOT else 'MANCANTE - BOT NON PARTE'}")
print(f"CHAT_ID: {'OK' if CHAT else 'MANCANTE'}")
print(f"API_FOOTBALL_KEY: {'OK' if KEY else 'MANCANTE'}")

ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)

@app.route('/')
def home():
    return f"BOT V38 MINIMAL LIVE {datetime.now(ITALY).strftime('%H:%M')} - BOT:{'OK' if BOT else 'NO'}", 200

TAST = json.dumps({
    "keyboard": [
        ["Serie A", "Serie B", "Inghilterra"],
        ["DOPPIA 90%"],
        ["BOLLA EUROPA 33 NAZIONI"],
        ["STATUS"]
    ],
    "resize_keyboard": True
})

def tg(m, cid=None, keys=False):
    try:
        if not BOT:
            print("TG: NO BOT_TOKEN, non invio")
            return
        cid = cid or CHAT
        if not cid:
            return
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        pay = {"chat_id": cid, "text": m, "parse_mode": "HTML"}
        if keys:
            pay["reply_markup"] = json.loads(TAST)
        requests.post(url, json=pay, timeout=20)
        print(f"TG inviato a {cid}")
    except Exception as e:
        print(f"TG ERROR: {e}")

def poll():
    last_id = 0
    print("POLL START")
    try:
        if BOT:
            requests.get(f"https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except:
        pass

    while True:
        try:
            if not BOT:
                print("POLL: aspetto BOT_TOKEN...")
                time.sleep(60)
                continue
            base = f"https://api.telegram.org/bot{BOT}"
            r = requests.get(f"{base}/getUpdates?offset={last_id+1}&timeout=20", timeout=30).json()
            if r.get("ok"):
                for u in r.get("result", []):
                    last_id = u["update_id"]
                    msg = u.get("message", {})
                    txt = (msg.get("text") or "").strip()
                    if not txt:
                        continue
                    cid = msg.get("chat", {}).get("id")
                    low = txt.lower()
                    print(f"Ricevuto: {low} da {cid}")

                    if "/start" in low or "accendi" in low:
                        tg("✅ V38 MINIMAL ONLINE\n\nSe leggi questo, Render è OK\nOra ti carico il resto con DOPPIA 90% + BOLLA 33", cid, True)
                    elif "status" in low:
                        tg(f"STATUS V38 OK\nOra: {datetime.now(ITALY).strftime('%H:%M')} Italia\nBOT: {'OK' if BOT else 'NO'}\nKEY: {'OK' if KEY else 'NO'}", cid, True)
                    elif "doppia" in low or "bolla" in low or "serie" in low:
                        tg(f"Ricevuto {txt} - sto caricando il motore completo tra 1 minuto, ora testo solo che rimanga live", cid, True)
        except Exception as e:
            print(f"POLL ERROR: {e}")
            traceback.print_exc()
        time.sleep(3)

threading.Thread(target=poll, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"FLASK START su porta {port}")
    # Questo deve rimanere live per forza
    tg("✅ V38 MINIMAL AVVIATO - Se leggi questo su Telegram, Render è OK", keys=True)
    app.run(host='0.0.0.0', port=port)
