import os, time, threading, requests, asyncio, datetime
from flask import Flask
from telegram.ext import Application, CommandHandler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
@app.route('/')
def home(): return "DAMI V7 FINALE - 90 SEC - 7200"

memoria = {}
chiamate = 0
schedina_fatta = None

async def start(update, context):
    context.application.bot_data["chat_id"] = update.effective_chat.id
    await update.message.reply_text(
        f"🔥 V7 FINALE ATTIVO!\nChiamate: {chiamate}/7200\n90 sec x 10 partite calde\n\n"
        "Dentro c'è tutto:\n"
        "1. ⚠️ SEGNALE 0.5 PRIMA\n"
        "2. 🔥 GOL FATTO\n"
        "3. 💀 MORTA 0-0\n"
        "4. 🔥 CALDA 6 tiri entro 60°\n"
        "5. 🟥 ROSSO 1° TEMPO\n"
        "6. 🎟️ SCHEDINA 10:00\n\n"
        "7040 chiamate/giorno - spremiamo tutto."
    )

def api_get(url):
    global chiamate
    h = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=h, timeout=20)
    chiamate += 1
    print(f"[{chiamate}/7200] {url[-30:]}")
    return r.json()

def loop(app_bot):
    global schedina_fatta, chiamate
    while True:
        try:
            now = datetime.datetime.now()
            if now.hour == 0 and now.minute < 3:
                chiamate = 0

            # SCHEDINA 10:00
            if now.hour == 10 and now.minute < 3 and schedina_fatta!= now.date():
                try:
                    data = api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
                    picks = []
                    for f in data.get("response",[]):
                        lg = f["league"]["name"]
                        if any(x in lg for x in ["Premier","Serie A","La Liga","Bundesliga","Ligue 1"]):
                            picks.append(f"{f['teams']['home']['name']} - {f['teams']['away']['name']} -> 1X @1.15")
                        if len(picks) >= 5: break
                    if picks:
                        msg = f"🎟️ SCHEDINA 10:00 QUOTA 1.77\n\n" + "\n".join([f"{i+1}. {p}" for i,p in enumerate(picks)])
                        chat_id = app_bot.bot_data.get("chat_id")
                        if chat_id:
                            asyncio.run(app_bot.bot.send_message(chat_id=chat_id, text=msg))
                        schedina_fatta = now.date()
                except Exception as e:
                    print(f"err schedina {e}")

            if chiamate > 7000:
                print("7000 raggiunte, dormo 1h")
                time.sleep(3600)
                continue

            data = api_get("https://v3.football.api-sports.io/fixtures?live=all")
            lives = data.get("response", [])

            lives_00 = [f for f in lives if f["goals"]["home"]==0 and f["goals"]["away"]==0]
            lives_00 = sorted(lives_00, key=lambda x: x["fixture"]["status"]["elapsed"] or 0, reverse=True)[:10]

            print(f"LIVE 0-0: {len(lives_00)}/{len(lives)} | Chiamate {chiamate}/7200")

            for f in lives_00:
                try:
                    fid = f["fixture"]["id"]
                    elapsed = f["fixture"]["status"]["elapsed"] or 0
                    if elapsed < 25 or elapsed > 88: continue

                    home = f["teams"]["home"]["name"]; away = f["teams"]["away"]["name"]
                    league = f["league"]["name"]
                    gh = f["goals"]["home"] or 0; ga = f["goals"]["away"] or 0

                    old = memoria.get(fid, {"tiri":0,"gol":0,"avv_gol":False,"avv_6":False,"avv_morta":False,"rosso":False})

                    # ROSSO 1T
                    if elapsed <= 45 and not old["rosso"]:
                        ev_data = api_get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}")
                        for ev in ev_data.get("response",[]):
                            if ev["type"]=="Card" and "Red" in ev["detail"]:
                                msg = f"🟥 ROSSO 1° TEMPO ({ev['time']['elapsed']}')\n{home} - {away}\n{league}\n{ev['player']['name']}"
                                chat_id = app_bot.bot_data.get("chat_id")
                                if chat_id: asyncio.run(app_bot.bot.send_message(chat_id=chat_id, text=msg))
                                old["rosso"]=True
                                break

                    stats_data = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    stats = stats_data.get("response", [])
                    tiri = 0; att = 0
                    for ts in stats:
                        for s in ts["statistics"]:
                            if s["type"]=="Shots on Goal": tiri+=s["value"] or 0
                            if s["type"]=="Dangerous Attacks": att+=s["value"] or 0

                    chat_id = app_bot.bot_data.get("chat_id")

                    # 1. SEGNALE PRIMA 0.5
                    if not old["avv_gol"] and tiri > old["tiri"] and tiri>=3 and tiri<=7 and att>25 and elapsed>=30:
                        msg = f"⚠️ SEGNALE 0.5 ({elapsed}')\n{home} - {away}\n{league}\nTiri {old['tiri']}->{tiri} Att {att}\n👉 ENTRA ORA!"
                        if chat_id: asyncio.run(app_bot.bot.send_message(chat_id=chat_id, text=msg))
                        old["avv_gol"]=True

                    # 2. CALDA 6 TIRI ENTRO 60
                    if not old["avv_6"] and elapsed<=60 and tiri>=6:
                        msg = f"🔥 CALDA 6 TIRI ENTRO 60° ({elapsed}')\n{home} - {away}\nTiri: {tiri}\nSTA SPINGENDO!"
                        if chat_id: asyncio.run(app_bot.bot.send_message(chat_id=chat_id, text=msg))
                        old["avv_6"]=True

                    # 3. MORTA
                    if not old["avv_morta"] and elapsed>=65 and tiri<=2:
                        msg = f"💀 MORTA 0-0 ({elapsed}')\n{home} - {away}\nTiri {tiri} - MORTA"
                        if chat_id: asyncio.run(app_bot.bot.send_message(chat_id=chat_id, text=msg))
                        old["avv_morta"]=True

                    old["tiri"]=tiri
                    memoria[fid]=old
                    time.sleep(0.4)

                except Exception as e:
                    print(f"err {e}"); continue

            print(f"Giro finito - dormo 90 sec | {chiamate}/7200")
            time.sleep(90)

        except Exception as e:
            print(f"Err loop {e}"); time.sleep(30)

def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: loop(application), daemon=True).start()
    print("V7 FINALE 90 SEC PARTITO")
    await application.run_polling()

if __name__ == "__main__": asyncio.run(main())
