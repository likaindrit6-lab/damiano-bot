
import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V36 LIVE - TUTTE LE LEGHE - ROSSO + CALDA", 200

# Legge le TUE chiavi esatte come le hai su Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")

print(f"TOKEN OK: {bool(TELEGRAM_TOKEN)}")
print(f"API KEY OK: {bool(API_FOOTBALL_KEY)}")
print(f"CHAT_ID OK: {bool(CHAT_ID)}")

gia_rossi = set()
gia_calde = set()

def check_partite():
    while True:
        try:
            if not API_FOOTBALL_KEY:
                print("Manca API_FOOTBALL_KEY, aspetto 90s")
                time.sleep(90)
                continue

            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            url = "https://v3.football.api-sports.io/fixtures?live=all"
            r = requests.get(url, headers=headers, timeout=15)
            data = r.json()
            fixtures = data.get("response", [])
            print(f"V36: {len(fixtures)} LIVE - consumo 1 token")

            for f in fixtures:
                fid = f["fixture"]["id"]
                minute = f["fixture"]["status"].get("elapsed", 0)
                if not minute or minute < 1:
                    continue
                
                home = f["teams"]["home"]["name"]
                away = f["teams"]["away"]["name"]
                gh = f["goals"]["home"]
                ga = f["goals"]["away"]

                # SOLO 0-0
                if gh != 0 or ga != 0:
                    continue

                score = f"{home} 0-0 {away}"

                # 1. ROSSO PRIMA DEL 60'
                if minute < 60:
                    try:
                        url_ev = f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}"
                        rev = requests.get(url_ev, headers=headers, timeout=10)
                        for ev in rev.json().get("response", []):
                            if ev.get("type") == "Card" and "red" in str(ev.get("detail","")).lower():
                                ev_min = ev.get("time", {}).get("elapsed", 0)
                                if ev_min and ev_min < 60:
                                    key = f"rosso_{fid}_{ev_min}"
                                    if key not in gia_rossi and TELEGRAM_TOKEN and CHAT_ID:
                                        import telebot
                                        bot_tmp = telebot.TeleBot(TELEGRAM_TOKEN)
                                        msg = f"🔴 ROSSO AL {ev_min}'\n{score}\nMin {minute}' - ENTRA 0-0!"
                                        bot_tmp.send_message(CHAT_ID, msg)
                                        gia_rossi.add(key)
                                        print(f"INVIATO ROSSO: {score}")
                    except Exception as e:
                        print(f"Err ev: {e}")

                # 2. PARTITA CALDA
                if minute > 25:
                    try:
                        url_st = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}"
                        rs = requests.get(url_st, headers=headers, timeout=10)
                        tot = 0
                        for ts in rs.json().get("response", []):
                            for st in ts.get("statistics", []):
                                if st.get("type") == "Total Shots":
                                    try:
                                        tot += int(st.get("value") or 0)
                                    except:
                                        pass
                        if tot >= 10:
                            key = f"calda_{fid}"
                            if key not in gia_calde and TELEGRAM_TOKEN and CHAT_ID:
                                import telebot
                                bot_tmp = telebot.TeleBot(TELEGRAM_TOKEN)
                                msg = f"🔥 CALDA 0-0 al {minute}'\n{score}\n{tot} tiri totali!"
                                bot_tmp.send_message(CHAT_ID, msg)
                                gia_calde.add(key)
                                print(f"INVIATA CALDA: {score} {tot} tiri")
                    except Exception as e:
                        print(f"Err st: {e}")

            time.sleep(90)

        except Exception as e:
            print(f"Errore V36: {e}")
            time.sleep(90)

def run_bot():
    try:
        if not TELEGRAM_TOKEN:
            print("Bot Telegram non parte - manca token, ma Flask resta ON")
            return
        import telebot
        bot = telebot.TeleBot(TELEGRAM_TOKEN)
        @bot.message_handler(commands=['start'])
        def start(m):
            bot.reply_to(m, f"V36 ATTIVO!\nTuo CHAT_ID: {m.chat.id}\nMettilo su Render se diverso\nControllo ogni 90s - Tutte le leghe")
        bot.infinity_polling()
    except Exception as e:
        print(f"Err Telegram: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=check_partite, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
