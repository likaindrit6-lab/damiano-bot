
import os, time, threading, requests, telebot
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)
gia_inviate = set()

def get_live():
    try:
        url = "https://v3.football.api-sports.io/fixtures?live=all"
        headers = {"x-apisports-key": API_KEY}
        r = requests.get(url, headers=headers, timeout=20)
        return r.json().get("response", [])
    except Exception as e:
        print(f"Errore live: {e}")
        return []

def get_stats(fid):
    try:
        url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}"
        headers = {"x-apisports-key": API_KEY}
        r = requests.get(url, headers=headers, timeout=20)
        return r.json()
    except:
        return {}

def analizza(fix, stats_data):
    try:
        minute = fix['fixture']['status']['elapsed'] or 0
        gh = fix['goals']['home'] or 0
        ga = fix['goals']['away'] or 0
        home = fix['teams']['home']['name']
        away = fix['teams']['away']['name']
        league = fix['league']['name']
        fid = fix['fixture']['id']

        if minute < 45 or minute > 85: return None
        if gh + ga > 2: return None

        if not stats_data.get('response') or len(stats_data['response']) < 2: return None
        sh = {x['type']: x['value'] for x in stats_data['response'][0]['statistics']}
        sa = {x['type']: x['value'] for x in stats_data['response'][1]['statistics']}

        tot_shots = (sh.get('Total Shots') or 0) + (sa.get('Total Shots') or 0)
        tot_sot = (sh.get('Shots on Goal') or 0) + (sa.get('Shots on Goal') or 0)
        tot_corners = (sh.get('Corner Kicks') or 0) + (sa.get('Corner Kicks') or 0)
        tot_dang = (sh.get('Dangerous Attacks') or 0) + (sa.get('Dangerous Attacks') or 0)

        segnale = None
        if tot_shots >= 12 and tot_sot >= 4 and tot_dang >= 60 and tot_corners >= 6:
            segnale = "CALDA"
        elif tot_shots >= 15 and tot_sot >= 5 and minute >= 70:
            segnale = "ROSSO"
        elif tot_shots < 5 and tot_dang < 30 and minute > 68:
            segnale = "MORTA"

        if segnale:
            icon = "🔥 CALDA" if segnale=="CALDA" else "🔴 ROSSO" if segnale=="ROSSO" else "💤 MORTA"
            return {
                "id": fid,
                "segnale": segnale,
                "text": f"{icon} {minute}' {home} {gh}-{ga} {away}\n🏆 {league}\n📊 Tiri: {tot_shots} ({tot_sot} in porta) | Angoli: {tot_corners} | Pericolosi: {tot_dang}"
            }
        return None
    except: return None

def loop_90s():
    time.sleep(10)
    if CHAT_ID:
        try:
            bot.send_message(int(CHAT_ID), "✅ V22 LIVE DAMI!\nCompatibile con le tue librerie di prima\nControllo ogni 90 sec attivo\nLogica CALDA/MORTA/ROSSO dentro")
        except Exception as e:
            print(e)

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] CHECK 90s", flush=True)
            lives = get_live()[:12]
            print(f"Live: {len(lives)}", flush=True)
            for fix in lives:
                fid = fix['fixture']['id']
                if fid in gia_inviate: continue
                stats = get_stats(fid)
                time.sleep(1.5)
                res = analizza(fix, stats)
                if res and res['segnale'] in ['CALDA','ROSSO']:
                    bot.send_message(int(CHAT_ID), res['text'])
                    gia_inviate.add(fid)
            if len(gia_inviate) > 120: gia_inviate.clear()
        except Exception as e:
            print(f"Errore loop: {e}", flush=True)
        time.sleep(90)

@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.reply_to(m, "✅ V22 attivo ogni 90 sec!")

# Avvia loop in background
threading.Thread(target=loop_90s, daemon=True).start()

print("V22 AVVIATO con pyTelegramBotAPI", flush=True)
bot.infinity_polling()
