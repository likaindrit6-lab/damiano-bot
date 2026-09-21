
import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V36.1 ANTI-409 - SOLO 1 ISTANZA", 200

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")

print(f"TOKEN OK: {bool(TELEGRAM_TOKEN)}")
print(f"CHAT_ID: {CHAT_ID}")

gia_rossi = set()
gia_calde = set()

def check_partite():
    while True:
        try:
            if not API_FOOTBALL_KEY:
                time.sleep(90)
                continue
            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            url = "https://v3.football.api-sports.io/fixtures?live=all"
            r = requests.get(url, headers=headers, timeout=15)
            fixtures = r.json().get("response", [])
            print(f"V36.1: {len(fixtures)} LIVE - OK")
            
            for f in fixtures:
                fid = f["fixture"]["id"]
                minute = f["fixture"]["status"].get("elapsed", 0)
                if not minute: continue
                if f["goals"]["home"] !=0 or f["goals"]["away"] !=0: continue
                home = f["teams"]["home"]["name"]
                away = f["teams"]["away"]["name"]
                score = f"{home} 0-0 {away}"
                
                if minute < 60:
                    try:
                        url_ev = f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}"
                        rev = requests.get(url_ev, headers=headers, timeout=10)
                        for ev in rev.json().get("response", []):
                            if ev.get("type")=="Card" and "red" in str(ev.get("detail","")).lower():
                                ev_min = ev.get("time",{}).get("elapsed",0)
                                if ev_min and ev_min < 60:
                                    key = f"rosso_{fid}_{ev_min}"
                                    if key not in gia_rossi and TELEGRAM_TOKEN and CHAT_ID:
                                        import telebot
                                        bt = telebot.TeleBot(TELEGRAM_TOKEN)
                                        bt.send_message(CHAT_ID, f"🔴 ROSSO AL {ev_min}'\n{score}\nMin {minute}' - ENTRA 0-0!")
                                        gia_rossi.add(key)
                    except: pass
            time.sleep(90)
        except Exception as e:
            print(f"Errore check: {e}")
            time.sleep(90)

def run_bot():
    import telebot
    import time as t
    while True:
        try:
            if not TELEGRAM_TOKEN:
                print("Manca TOKEN, aspetto")
                t.sleep(60)
                continue
            bot = telebot.TeleBot(TELEGRAM_TOKEN)
            # FIX 409 - Cancella l'altro bot
            try:
                bot.delete_webhook(drop_pending_updates=True)
                print("Webhook cancellato, ora sono SOLO IO!")
                t.sleep(2)
            except: pass

            @bot.message_handler(commands=['start'])
            def start(m):
                bot.reply_to(m, f"V36.1 ANTI-409 ATTIVO!\nCHAT_ID: {m.chat.id}\nOra sono uno solo!")

            print("Bot polling parte - istanza unica")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Riavvio bot tra 10s per 409: {e}")
            t.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=check_partite, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
