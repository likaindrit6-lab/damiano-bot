
import os, threading, requests, time, csv
from flask import Flask
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot V2 LIVE - 90s OK - Calda/Morta/Angoli/Schedina"

TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("API_KEY")
CHATS = set()
INVIATE = set()

# Memoria segnali
segnali_attivi = {} # fixture_id -> dati
schedina_oggi = []
storico_file = "storico.csv"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

def salva_storico(tipo, partita, esito, minuti):
    try:
        nuovo = not os.path.exists(storico_file)
        with open(storico_file, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            if nuovo: w.writerow(["data","tipo","partita","esito","min"])
            w.writerow([datetime.now().strftime("%d/%m %H:%M"), tipo, partita, esito, minuti])
    except: pass

async def send_all(msg):
    for chat_id in list(CHATS):
        try:
            await app_bot.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        except: pass

def send_all_sync(msg):
    # per thread non-async
    import asyncio
    for chat_id in list(CHATS):
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

def get_live():
    try:
        r = requests.get(f"{BASE_URL}/fixtures?live=all", headers=headers, timeout=10).json()
        return r.get("response", [])
    except: return []

def get_stats(fid):
    try:
        r = requests.get(f"{BASE_URL}/fixtures/statistics?fixture={fid}", headers=headers, timeout=10).json()
        return r.get("response", [])
    except: return []

def check_segnali_attivi():
    for fid in list(segnali_attivi.keys()):
        if not str(fid).isdigit(): continue
        data = segnali_attivi[fid]
        if datetime.now() > data["scadenza"]:
            if "CALDA" in data["tipo"]:
                send_all_sync(f"❌ Segnale scaduto {data['partita']} - niente gol dal {data['minuto']}'")
                salva_storico(data["tipo"], data["partita"], "PERSA", 15)
            del segnali_attivi[fid]
            continue
        try:
            r = requests.get(f"{BASE_URL}/fixtures?id={fid}", headers=headers, timeout=10).json()
            if not r["response"]: continue
            match = r["response"][0]
            goals_now = (match["goals"]["home"] or 0) + (match["goals"]["away"] or 0)
            if goals_now > data["goals"]:
                minuti_imp = match["fixture"]["status"]["elapsed"] - data["minuto"]
                send_all_sync(f"⚽ *GOOOOL! SEGNALE PRESO!*\n{data['partita']} {match['goals']['home']}-{match['goals']['away']} al {match['fixture']['status']['elapsed']}'\nSegnale {data['tipo']} del {data['minuto']}' -> GOL in {minuti_imp} min!")
                salva_storico(data["tipo"], data["partita"], "VINTA", minuti_imp)
                del segnali_attivi[fid]
                # Check angoli
                if "ANGOLO" in data["tipo"]:
                    salva_storico(data["tipo"], data["partita"], "VINTA", minuti_imp)
        except: pass

def schedina_mattina():
    global schedina_oggi
    try:
        oggi = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(f"{BASE_URL}/fixtures?date={oggi}", headers=headers, timeout=10).json()
        fixtures = [f for f in r.get("response", []) if f["fixture"]["status"]["short"] == "NS"][:30]
        if len(fixtures) >= 3:
            picks = fixtures[2:5]
            msg = "📋 *SCHEDINA DEL GIORNO - Quota 1.72*\n\n"
            schedina_oggi = []
            for p in picks:
                nome = f"{p['teams']['home']['name']} - {p['teams']['away']['name']}"
                msg += f"• {nome} Over 0.5\n"
                schedina_oggi.append({"id": p["fixture"]["id"], "nome": nome, "fatto": False, "gol": False})
            msg += "\nGiocala e ti avviso io se VINTA/PERSA!"
            send_all_sync(msg)
    except Exception as e:
        print(e)

def check_scontrino_finale():
    global schedina_oggi
    if not schedina_oggi: return
    try:
        # controlla se tutte finite
        finite = 0
        vinte = 0
        for s in schedina_oggi:
            r = requests.get(f"{BASE_URL}/fixtures?id={s['id']}", headers=headers, timeout=10).json()
            if not r["response"]: continue
            m = r["response"][0]
            status = m["fixture"]["status"]["short"]
            if status == "FT":
                finite += 1
                goals = (m["goals"]["home"] or 0) + (m["goals"]["away"] or 0)
                if goals >= 1:
                    vinte += 1
        if finite == len(schedina_oggi) and finite>0:
            if vinte == len(schedina_oggi):
                send_all_sync(f"✅ *SCHEDINA VINTA!*\n{vinte} su {finite} prese!\nQuota 1.72 portata a casa!")
            else:
                send_all_sync(f"❌ *SCHEDINA PERSA*\n{vinte} su {finite} - ci rifacciamo domani!")
            schedina_oggi = [] # reset
    except: pass

def loop_bot():
    send_all_sync("🤖 *BOT V2 AVVIATO 24/24*\nCalda 1T/2T + Morta + Angoli + Rosso + Schedina VINTA/PERSA\nFascia calda: 90sec - Fascia notte: 3min")
    ultima_schedina = ""
    while True:
        try:
            ora = datetime.now()
            if ora.hour == 9 and ora.minute < 10 and ultima_schedina!= ora.strftime("%Y-%m-%d"):
                schedina_mattina()
                ultima_schedina = ora.strftime("%Y-%m-%d")

            live = get_live()
            for match in live:
                fid = match["fixture"]["id"]
                minuto = match["fixture"]["status"]["elapsed"] or 0
                if not (20 <= minuto <= 85): continue
                nome = f"{match['teams']['home']['name']} - {match['teams']['away']['name']}"
                gh = match["goals"]["home"] or 0
                ga = match["goals"]["away"] or 0
                tot_gol = gh+ga

                stats = get_stats(fid)
                if not stats: continue
                shots_on = 0
                shots_total = 0
                corners = 0
                red = 0
                for ts in stats:
                    for s in ts["statistics"]:
                        if s["type"] == "Shots on Goal": shots_on += s["value"] or 0
                        if s["type"] == "Total Shots": shots_total += s["value"] or 0
                        if s["type"] == "Corner Kicks": corners += s["value"] or 0
                        if s["type"] == "Red Cards": red += s["value"] or 0

                if 20 <= minuto <= 35 and shots_on >= 4 and fid not in segnali_attivi:
                    send_all_sync(f"🔥 *CALDA 1° TEMPO {minuto}'*\n{nome}\n{shots_on} tiri in porta - Sta per segnare\n{gh}-{ga}")
                    segnali_attivi[fid] = {"tipo":"CALDA_1T","partita":nome,"minuto":minuto,"goals":tot_gol,"scadenza":datetime.now()+timedelta(minutes=15)}
                if 55 <= minuto <= 85 and shots_on >= 6 and fid not in segnali_attivi:
                    send_all_sync(f"🔥 *CALDA 2° TEMPO {minuto}'*\n{nome}\n{shots_on} tiri in porta - GOL IMMINENTE\n{gh}-{ga}")
                    segnali_attivi[fid] = {"tipo":"CALDA_2T","partita":nome,"minuto":minuto,"goals":tot_gol,"scadenza":datetime.now()+timedelta(minutes=15)}
                if 55 <= minuto <= 70 and shots_total <= 4 and fid not in segnali_attivi:
                    send_all_sync(f"💀 *MORTA {minuto}'*\n{nome}\nSolo {shots_total} tiri - UNDER 2.5\n{gh}-{ga}")
                    segnali_attivi[fid] = {"tipo":"MORTA","partita":nome,"minuto":minuto,"goals":tot_gol,"scadenza":datetime.now()+timedelta(minutes=90)}
                if minuto <= 45 and red >= 1 and f"rosso_{fid}" not in segnali_attivi:
                    send_all_sync(f"🟥 *ROSSO 1° TEMPO {minuto}'*\n{nome}\nEspulsione! Over 0.5 2T")
                    segnali_attivi[f"rosso_{fid}"] = {"tipo":"ROSSO","scadenza":datetime.now()+timedelta(minutes=90)}
                if 25 <= minuto <= 40 and corners >= 6 and fid not in segnali_attivi:
                    send_all_sync(f"🚩 *ANGOLI CALDI {minuto}'*\n{nome}\n{corners} angoli")
                    segnali_attivi[fid] = {"tipo":"ANGOLO_CALDO","partita":nome,"minuto":minuto,"goals":corners,"corners":corners,"scadenza":datetime.now()+timedelta(minutes=12)}

            check_segnali_attivi()
            check_scontrino_finale()

            if 14 <= datetime.now().hour <= 23:
                time.sleep(90)
            else:
                time.sleep(180)
        except Exception as e:
            print("err loop", e)
            time.sleep(30)

# Telegram commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHATS.add(update.effective_chat.id)
    await update.message.reply_text("Bot V2 attivo! Riceverai: Calda, Morta, Angoli, GOL FATTO e Schedina VINTA/PERSA 9:00")

app_bot = Application.builder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))

def run_telegram():
    app_bot.run_polling()

threading.Thread(target=loop_bot, daemon=True).start()
threading.Thread(target=run_telegram, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
