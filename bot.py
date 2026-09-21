
import os
import time
import threading
import requests
from flask import Flask
import telebot

# --- CONFIG ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Per UptimeRobot - NON TOCCARE - tiene il bot sveglio
@app.route('/')
def home():
    return "BOT V35 ONLINE 24/7 - TUTTE LE LEGHE", 200

gia_inviati_rossi = set()
gia_inviate_calde = set()

def check_partite():
    while True:
        try:
            print("V35: Controllo TUTTE le partite ogni 90 sec...")
            
            if not API_FOOTBALL_KEY:
                print("MANCA API_FOOTBALL_KEY su Render!")
                time.sleep(90)
                continue

            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            
            # TUTTE LE PARTITE DEL MONDO LIVE
            url = "https://v3.football.api-sports.io/fixtures?live=all"
            r = requests.get(url, headers=headers, timeout=15)
            data = r.json()
            fixtures = data.get("response", [])
            
            print(f"V35: Trovate {len(fixtures)} LIVE")

            for f in fixtures:
                fixture = f.get("fixture", {})
                fixture_id = fixture.get("id")
                minute = fixture.get("status", {}).get("elapsed", 0)
                if not minute:
                    continue

                teams = f.get("teams", {})
                home = teams.get("home", {}).get("name", "")
                away = teams.get("away", {}).get("name", "")
                goals = f.get("goals", {})
                g_home = goals.get("home", 0)
                g_away = goals.get("away", 0)

                # SOLO 0-0
                if g_home != 0 or g_away != 0:
                    continue
