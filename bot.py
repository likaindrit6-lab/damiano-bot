
import time, requests, datetime
from datetime import date

API_KEY = "LA_TUA_API_KEY"
HEADERS = {"x-apisports-key": API_KEY}

# MEMORIA
calde_tiri_segnalate = set()
calde_angoli_segnalate = set()
morti_segnalate = set()
schedine_inviate_oggi = None

def orario_attivo():
    h = datetime.datetime.now().hour
    return h >= 9 # 9:00 - 23:59 attivo, 0-8 dorme

def invia_messaggio(testo):
    print(testo) # qui metti il tuo invio WhatsApp/Telegram
    # requests.post("tuo_bot_telegram", data={"text": testo})

def get_live():
    # 1 TOKEN
    r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS)
    return r.json().get('response', [])

def get_stats(fixture_id):
    # 1 TOKEN a chiamata
    r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}", headers=HEADERS)
    # ritorna tiri, angoli, minuti, gol, se c'e' nuovo gol
    return {"tiri": 6, "angoli": 5, "minuti": 47, "gol": "1-0", "nuovo_gol": False, "nome": f"Match {fixture_id}"}

def schedine_ore_9():
    # 20 TOKEN circa - analizza ultime 5 partite
    # 1. Quota 1.7/1.8 - prendi le 5 con xG piu' alto
    # 2. Calda - squadre con 2 gol di media nelle ultime 5
    invia_messaggio("📋 SCHEDINA 09:00 - QUOTA 1.7: [qui 5 partite]")
    invia_messaggio("🔥 SCHEDINA 09:00 - CALDA (2 gol media): [qui squadre calde di oggi + notturne]")

# LOOP PRINCIPALE
while True:
    ora = datetime.datetime.now()
    
    # SCHEDINE 09:00 - una volta al giorno
    if ora.hour == 9 and ora.minute < 2 and schedine_inviate_oggi != date.today():
        schedine_ore_9()
        schedine_inviate_oggi = date.today()

    if not orario_attivo():
        print("💤 Dormo fino alle 09:00")
        time.sleep(60*60)
        continue

    print(f"🔍 Controllo 90sec... {ora.strftime('%H:%M:%S')}")
    live_matches = get_live() # 1 TOKEN

    for m in live_matches:
        fid = m['fixture']['id']
        stats = get_stats(fid) # 1 TOKEN a match
        tiri = stats['tiri']
        angoli = stats['angoli']
        minuti = stats['minuti']

        # 1. CALDA TIRI - SEPARATA
        if minuti <= 50 and tiri >= 6 and fid not in calde_tiri_segnalate:
            invia_messaggio(f"🔥 CALDA TIRI! {stats['nome']} - {tiri} tiri al {minuti}'")
            calde_tiri_segnalate.add(fid)

        # 2. CALDA ANGOLI - SEPARATA
        if minuti <= 50 and angoli >= 5 and fid not in calde_angoli_segnalate:
            invia_messaggio(f"🚩 CALDA ANGOLI! {stats['nome']} - {angoli} angoli al {minuti}'")
            calde_angoli_segnalate.add(fid)

        # 3. GOL NELLE CALDE (entrambe)
        if (fid in calde_tiri_segnalate or fid in calde_angoli_segnalate) and stats['nuovo_gol']:
            invia_messaggio(f"⚽️ GOOOL in CALDA! {stats['nome']} {stats['gol']} al {minuti}'")

        # 4. MORTA
        if minuti == 60 and tiri <= 3 and fid not in morti_segnalate:
            invia_messaggio(f"💀 MORTA - DA EVITARE! {stats['nome']} - solo {tiri} tiri al 60'")
            morti_segnalate.add(fid)

    time.sleep(90) # OGNI 90 SECONDI FISSO
