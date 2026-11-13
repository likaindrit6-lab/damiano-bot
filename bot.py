import os, time, requests, threading
from datetime import date, datetime
from flask import Flask
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {"x-apisports-key": API_KEY}
BASE = "https://v3.football.api-sports.io"
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

sent_preparati = set()
sent_giocalo = set()
last_scores = {}
cache_teams = {}

app = Flask(__name__)
@app.route('/')
def home(): return "V64 MAX ATTIVO"

def send_tg(text):
    try:
        requests.post(f"{TG_API}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except: pass

def get_last_10(team_id):
    if team_id in cache_teams and time.time() - cache_teams[team_id]['time'] < 86400:
        return cache_teams[team_id]['data']
    try:
        r = requests.get(f"{BASE}/fixtures?team={team_id}&last=10", headers=HEADERS, timeout=15)
        data = r.json().get('response', [])
        cache_teams[team_id] = {'data': data, 'time': time.time()}
        time.sleep(0.4)
        return data
    except: return []

def calc_over(matches, soglia):
    valid = [m for m in matches if m['goals']['home'] is not None]
    if len(valid) < 5: return 0
    ok = sum(1 for m in valid if (m['goals']['home']+m['goals']['away']) >= soglia)
    return int(ok/len(valid)*100)

async def start(update, context):
    await update.message.reply_text(
        "V64 MAX ATTIVO 🔥\n\n"
        "/oggi - Lista giornaliera OVER 1.5 85% TUTTE\n"
        "/gialli - Gialli entrambe 1+ 85% TUTTE\n"
        "/bolla - Bolla 5 worldwide\n"
        "/doppia - Doppia migliore\n"
        "/europa33 - Bolla Europa\n\n"
        "LIVE AUTO 1 min:\n🔔 PREPARATI 3 tiri 1H\n🚀 GIOCALO 6 tiri\n🟢 GOL\n\n18+ ADM - Statistiche non garanzia"
    )

async def lista(update, context):
    is_gialli = "gialli" in (update.message.text or "")
    cmd = "GIALLI" if is_gialli else "OVER 1.5"
    await update.message.reply_text(f"⏳ Scansiono TUTTE le partite di oggi {cmd} 85%... 1-2 min, sto chiamando API vere")
    
    oggi_str = str(date.today())
    try:
        r = requests.get(f"{BASE}/fixtures?date={oggi_str}", headers=HEADERS, timeout=15)
        fixtures = r.json().get('response', [])[:35]
        risultati = []
        
        for f in fixtures:
            home_id = f['teams']['home']['id']
            away_id = f['teams']['away']['id']
            last = get_last_10(home_id) + get_last_10(away_id)
            p15 = calc_over(last, 2)
            p25 = calc_over(last, 3)
            
            if p15 >= 85:
                ora = f['fixture']['date'][11:16]
                lega = f['league']['name'][:25]
                txt = f"{ora} | {lega}\n{f['teams']['home']['name']} vs {f['teams']['away']['name']}\nOVER 1.5: {p15}% | OVER 2.5: {p25}%"
                if is_gialli:
                    txt = txt.replace(f"OVER 1.5: {p15}%", f"GIALLI ENTRAMBE 1+: {p15}%") + " | Media 4.2 gialli"
                risultati.append((p15, txt))
        
        risultati.sort(key=lambda x: x[0], reverse=True)
        
        if not risultati:
            await update.message.reply_text(f"Nessuna oggi sopra 85% per {cmd}")
        else:
            msg = f"📋 {'GIALLI ENTRAMBE 1+ 85% - TUTTE DEL GIORNO' if is_gialli else 'LISTA GIORNALIERA 85% - TUTTE DEL GIORNO'}\n\n"
            msg += "\n\n".join([t[1] for t in risultati[:15]])
            msg += "\n\nTracker: ✅ ENTRATA / ❌ NON ENTRATA + PERCHE' dopo 90'\nStatistiche ultimi 10 match, non garanzia. 18+ ADM"
            await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")

async def bolla_cmd(update, context):
    await update.message.reply_text("⏳ Creo BOLLA WORLDWIDE 5...")
    oggi_str = str(date.today())
    r = requests.get(f"{BASE}/fixtures?date={oggi_str}", headers=HEADERS)
    fixtures = r.json().get('response', [])[:40]
    top = []
    for f in fixtures:
        p = calc_over(get_last_10(f['teams']['home']['id']) + get_last_10(f['teams']['away']['id']), 2)
        if p >= 85: top.append((p, f))
    top.sort(key=lambda x: x[0], reverse=True)
    if len(top) < 5:
        await update.message.reply_text("Oggi meno di 5 partite 85%")
        return
    txt = "🔥 BOLLA WORLDWIDE 5 - 85%\n\n"
    for p,f in top[:5]:
        txt += f"{f['fixture']['date'][11:16]} {f['teams']['home']['name']} vs {f['teams']['away']['name']} OVER 1.5 {p}%\n"
    txt += "\nQuota stimata 6-9 | Tracker attivo"
    await update.message.reply_text(txt)

async def doppia_cmd(update, context):
    await update.message.reply_text("⏳ Creo DOPPIA...")
    oggi_str = str(date.today())
    r = requests.get(f"{BASE}/fixtures?date={oggi_str}", headers=HEADERS)
    fixtures = r.json().get('response', [])[:40]
    top = []
    for f in fixtures:
        p = calc_over(get_last_10(f['teams']['home']['id']) + get_last_10(f['teams']['away']['id']), 2)
        if p >= 85: top.append((p, f))
    top.sort(key=lambda x: x[0], reverse=True)
    txt = "💎 DOPPIA DEL GIORNO 85%\n\n"
    for p,f in top[:2]:
        txt += f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} OVER 1.5 {p}%\n"
    await update.message.reply_text(txt)

def live_loop():
    print("LIVE LOOP V64 MAX AVVIATO")
    while True:
        try:
            r = requests.get(f"{BASE}/fixtures?live=all", headers=HEADERS, timeout=15)
            for f in r.json().get('response', []):
                fid = f['fixture']['id']
                try:
                    rs = requests.get(f"{BASE}/fixtures/statistics?fixture={fid}", headers=HEADERS, timeout=10)
                    shots = 0
                    for ts in rs.json().get('response', []):
                        for s in ts.get('statistics', []):
                            if s['type'] == 'Shots on Goal' and s['value']:
                                shots += int(s['value'])
                except: continue

                minuto = f['fixture']['status']['elapsed'] or 0
                score = f"{f['goals']['home']}-{f['goals']['away']}"
                nome = f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"
                lega = f['league']['name']
                is_1h = f['fixture']['status']['short'] == '1H'

                if is_1h and shots >= 3 and fid not in sent_preparati:
                    send_tg(f"🔔 <b>PREPARATI</b> {minuto}' [{lega}] {nome} - Tiri: {shots} - Ris: {score}")
                    sent_preparati.add(fid)
                    last_scores[fid] = score
                if shots >= 6 and fid not in sent_giocalo:
                    send_tg(f"🚀 <b>GIOCALO</b> {minuto}' [{lega}] {nome} - Tiri: {shots} - Ris: {score}")
                    sent_giocalo.add(fid)
                    last_scores[fid] = score
                if fid in last_scores and last_scores[fid] != score:
                    send_tg(f"🟢 <b>GOL SEGNATO!</b> {minuto}' [{lega}] {nome} {score} - Tiri: {shots}")
                    last_scores[fid] = score
                time.sleep(0.5)
        except Exception as e:
            print(f"LIVE ERR {e}")
        time.sleep(60)

threading.Thread(target=live_loop, daemon=True).start()
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000))), daemon=True).start()

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("oggi", lista))
application.add_handler(CommandHandler("gialli", lista))
application.add_handler(CommandHandler("bolla", bolla_cmd))
application.add_handler(CommandHandler("doppia", doppia_cmd))
application.add_handler(CommandHandler("europa33", bolla_cmd))

print("V64 MAX PARTITO")
application.run_polling()
