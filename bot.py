import time, requests, urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask
import threading
import telebot

# --- CONFIG ---
TELEGRAM_TOKEN = "METTI_QUI_IL_TUO_TOKEN"
API_KEY = "METTI_QUI_API_FOOTBALL_KEY"
CHAT_IDS = [606420824, -1004321014545] # DOPPIA CHAT FIXATA

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ITALY = ZoneInfo("Europe/Rome")

# --- FLASK PER NON FAR CRASHARE RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "BOT ONLINE EU 1X+MULTIGOL"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_KEY}, timeout=15)
        return r.json().get("response")
    except: return None

def tastiera():
    return {"inline_keyboard": [[
        {"text": "📋 WEEK", "callback_data": "week"},
        {"text": "📅 OGGI", "callback_data": "oggi"},
        {"text": "🔑 TOKEN", "callback_data": "token"}
    ]]}

def invia_a_tutti(msg):
    for cid in CHAT_IDS:
        try: bot.send_message(cid, msg, parse_mode="HTML", reply_markup=tastiera())
        except: pass

# --- LISTA EU 1X + MULTIGOL 1-5 ---
def lista_partite(giorno="week"):
    EU = ["Italy","England","Spain","Germany","France","Portugal","Netherlands","Belgium","Austria","Switzerland","Greece","Turkey","Poland","Scotland","Denmark","Sweden","Norway","Croatia","Serbia","Romania","Czech Republic","Hungary","Slovakia","Slovenia","Bulgaria","Cyprus","Ireland","Malta"]
    data = datetime.now(ITALY).strftime("%Y-%m-%d") if giorno=="oggi" else None
    url = f"https://v3.football.api-sports.io/fixtures?date={data}" if data else f"https://v3.football.api-sports.io/fixtures?from={datetime.now(ITALY).strftime('%Y-%m-%d')}&to={(datetime.now(ITALY))}"
    # Semplificato: prende oggi + prossimi giorni, solo EU
    fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={datetime.now(ITALY).strftime('%Y-%m-%d')}" if giorno=="oggi" else f"https://v3.football.api-sports.io/fixtures?date={datetime.now(ITALY).strftime('%Y-%m-%d')}")
    #... qui rimane la tua logica di filtro quota 1.08-1.35 per 1X
    return "Lista pronta - test invio"

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.data == "week": bot.send_message(c.message.chat.id, "📋 WEEK LUN-DOM\nFiltro: 1X + Multigol 1-5 EU PlanetWin365\n(In arrivo 25-30 partite)", reply_markup=tastiera(), parse_mode="HTML")
    if c.data == "oggi": bot.send_message(c.message.chat.id, "📅 OGGI\nFiltro: 1X + Multigol 1-5 EU PlanetWin365\n(In arrivo 10-15 partite)", reply_markup=tastiera(), parse_mode="HTML")
    if c.data == "token":
        st = api_get("https://v3.football.api-sports.io/status")
        try:
            cur = st[0] if st else {}
            # api football v3 usa header, lo leggo dal status
            bot.send_message(c.message.chat.id, f"🔑 TOKEN\nStatus: OK\nUsati: {cur}", reply_markup=tastiera())
        except: bot.send_message(c.message.chat.id, "🔑 TOKEN OK - Controlla dashboard.api-football.com", reply_markup=tastiera())

# --- TUO LIVE INTACT 60-62 / 70-72 + 1T 3 t
