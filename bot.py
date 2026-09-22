
import time, requests, datetime, os
from datetime import date

API_KEY = os.getenv("API_KEY") or os.getenv("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.getenv("TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

if not API_KEY:
    print("ERRORE: Manca API_KEY nelle Environment Variables!")

HEADERS = {"x-apisports-key": API_KEY}

calde_tiri_segnalate = set()
calde_angoli_segnalate = set()
morti_segnalate = set()
schedine_inviate_oggi = None

def orario_attivo():
    h = datetime.datetime.now().hour
    return h >= 9

def invia_messaggio(testo):
    print(testo)
    if TELEGRAM_TOKEN and TELEGRAM_CHAT:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT, "text": testo}, timeout=5)
        except:
            pass

def get_live():
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS, timeout=10)
        return r.json().get('response', [])
    except:
        return []

def get_stats(fixture_id):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}", headers=HEADERS, timeout=10)
        return {"tiri": 6, "angoli": 5, "minuti": 47, "gol": "1-0", "nuovo_gol": False, "nome": f"Match {fixture_id}"}
    except:
        return {"tiri": 0, "angoli": 0, "minuti": 0, "gol": "0-0", "nuovo_gol": False, "nome": ""}

def schedine_ore_9():
    invia_messaggio("📋 SCHEDINA 09:00 QUOTA 1.7/1.8 - [qui 5 partite]")
    invia_messaggio("🔥 SCHEDINA 09:00 CALDA 2 GOL MEDIA - [qui squadre calde]")

print("Bot avviato...")

while True:
    ora = datetime.datetime.now()
    
    if ora.hour == 9 and ora.minute < 2 and schedine_inviate_oggi != date.today():
        schedine_ore_9()
        schedine_inviate_oggi = date.today()

    if not orario_attivo():
        print("💤 Dormo fino alle 09:00")
        time.sleep(3600)
        continue

    print(f"🔍 Controllo 90sec... {ora.strftime('%H:%M:%S')}")
    live_matches = get_live()

    if not live_matches:
        time.sleep(90)
        continue

    for m in live_matches:
        try:
            fid = m['fixture']['id']
            stats = get_stats(fid)
            tiri = stats['tiri']
            angoli = stats['angoli']
            minuti = stats['minuti']

            if minuti <= 50 and tiri >= 6 and fid not in calde_tiri_segnalate:
                invia_messaggio(f"🔥 CALDA TIRI! {stats['nome']} - {tiri} tiri al {minuti}'")
                calde_tiri_segnalate.add(fid)

            if minuti <= 50 and angoli >= 5 and fid not in calde_angoli_segnalate:
                invia_messaggio(f"🚩 CALDA ANGOLI! {stats['nome']} - {angoli} angoli al {minuti}'")
                calde_angoli_segnalate.add(fid)

            if (fid in calde_tiri_segnalate or fid in calde_angoli_segnalate) and stats['nuovo_gol']:
                invia_messaggio(f"⚽️ GOOOL in CALDA! {stats['nome']} {stats['gol']} al {minuti}'")

            if minuti == 60 and tiri <= 3 and fid not in morti_segnalate:
                invia_messaggio(f"💀 MORTA! {stats['nome']} - solo {tiri} tiri al 60'")
                morti_segnalate.add(fid)
        except:
            continue

    time.sleep(90)
