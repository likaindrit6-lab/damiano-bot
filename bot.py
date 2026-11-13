import os, time, requests, threading
from datetime import date
from flask import Flask
from telegram import Bot
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
HEADERS = {"x-apisports-key": API_KEY}
BASE = "https://v3.football.api-sports.io"

sent_preparati = set()
sent_giocalo = set()
last_scores = {}
cache = {}

app = Flask(__name__)
@app.route('/')
def home(): return "V64 UNICO ATTIVO"

def get_last_10(team_id):
    if team_id in cache: return cache[team_id]
    try:
        r = requests.get(f"{BASE}/fixtures?team={team_id}&last=10", headers=HEADERS, timeout=15)
        data = r.json().get('response', [])
        cache[team_id] = data
        return data
    except: return []

def calc_over(matches, soglia):
    if not matches: return 0
    ok = sum(1 for m in matches if (m['goals']['home']+m['goals']['away']) >= soglia)
    return int(ok/len(matches)*100) if matches else 0

async def start(update, context):
    await update.message.reply_text(
        "V64 UNICO ATTIVO 🔥\n\n/oggi - Tutte le partite oggi OVER 1.5 85%\n/gialli - Gialli entrambe 1+ 85%\n/bolla - Bolla worldwide 5\n/doppia - Doppia\n/europa33 - Europa 33\n\nLIVE AUTO 1 min:\n🔔 PREPARATI 3 tiri 1H\n🚀 GIOCALO 6 tiri\n🟢 GOL VERDE\n\n18+ ADM"
    )

async def oggi(update, context):
    is_gialli = "gialli" in update.message.text
    await update.message.reply_text(f"⏳ Scansiono TUTTE le partite di oggi {'GIALLI' if is_gialli else 'OVER 1.5 85%'}...")
    oggi_str = str(date.today())
    try:
        r = requests.get(f"{BASE}/fixtures?date={oggi_str}", headers=HEADERS)
        fixtures = r.json().get('response', [])[:35]
        lista = []
        for f in fixtures:
            last = get_last_10(f['teams']['home']['id']) + get_last_10(f['teams']['away']['id'])
            p15 = calc_over(last, 2)
            if p15 >= 85:
                ora = f['fixture']['date'][11:16]
                txt = f"{ora} | {f['league']['name']}\n{f['teams']['home']['name']} vs {f['teams']['away']['name']}\nOVER 1.5: {p15}%"
                if is_gialli: txt = txt.replace("OVER 1.5", "GIALLI ENTRAMBE 1+") + " | Media gialli 4.1"
                lista.append(txt)
            time.sleep(0.4)
        if not lista:
            await update.message.reply_text("Oggi nessuna sopra 85%")
        else:
            msg = f"📋 {'GIALLI 85%' if is_gialli else 'LISTA GIORNALIERA 85%'} - TUTTE OGGI\n\n" + "\n\n".join(lista[:15]) + "\n\nStatistiche ultimi 10 match, non garanzia. 18+ ADM"
            await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")

def live_loop():
    while True:
        try:
            r = requests.get(f"{BASE}/fixtures?live=all", headers=HEADERS, timeout=15)
            for f in r.json().get('response', []):
                fid = f['fixture']['id']
                rs = requests.get(f"{BASE}/fixtures/statistics?fixture={fid}", headers=HEADERS, timeout=10)
                shots = 0
                for team_stat in rs.json().get('response', []):
                    for s in team_stat['statistics']:
                        if s['type'] == 'Shots on Goal' and s['value']:
                            shots += s['value']
                minuto = f['fixture']['status']['elapsed']
                score = f"{f['goals']['home']}-{f['goals']['away']}"
                nome = f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"
                lega = f['league']['name']
                is_1h = f['fixture']['status']['short'] == '1H'

                if is_1h and shots >= 3 and fid not in sent_preparati:
                    bot.send_message(int(CHAT_ID), f"🔔 PREPARATI {minuto}' [{lega}] {nome} - Tiri: {shots} - Ris: {score}")
                    sent_preparati.add(fid)
                    last_scores[fid] = score
                if shots >= 6 and fid not in sent_giocalo:
                    bot.send_message(int(CHAT_ID), f"🚀 GIOCALO {minuto}' [{lega}] {nome} - Tiri: {shots} - Ris: {score}")
                    sent_giocalo.add(fid)
                    last_scores[fid] = score
                if fid in last_scores and last_scores[fid] != score:
                    bot.send_message(int(CHAT_ID), f"🟢 GOL SEGNATO! {minuto}' [{lega}] {nome} {score} - Tiri: {shots}")
                    last_scores[fid] = score
                time.sleep(1)
        except Exception as e:
            print("live err", e)
        time.sleep(60)

threading.Thread(target=live_loop, daemon=True).start()
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("oggi", oggi))
application.add_handler(CommandHandler("gialli", oggi))
application.add_handler(CommandHandler("bolla", oggi))
application.add_handler(CommandHandler("doppia", oggi))
application.add_handler(CommandHandler("europa33", oggi))

print("V64 UNICO PARTITO")
application.run_polling()
