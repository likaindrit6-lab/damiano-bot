import os, time, requests
from datetime import datetime

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}

def send(t):
    if not TOKEN or not CHAT:
        print("ERRORE: TOKEN o CHAT_ID mancanti!")
        return
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t, "parse_mode": "Markdown"}, timeout=15)
        print(f"SEND: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"ERRORE SEND: {e}")

def is_orario_attivo():
    h = datetime.now().hour
    if h >= 8 or h < 2: return True
    return False

# ... LE TUE FUNZIONI get_stats, get_corner_minuti, calcola_prob UGUALI ...

def get_liste_10():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        odds_data = requests.get(f"https://v3.football.api-sports.io/odds?date={today}", headers=HEAD, timeout=25).json().get("response",[])
    except Exception as e:
        print(f"ERRORE ODDS CALCIO: {e}")
        return [], [], "Errore API calcio"
    # ... resto uguale ...

def get_basket_1Q():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        data = requests.get(f"https://v3.basketball.api-sports.io/odds?date={today}", headers=HEAD, timeout=25).json()
        print(f"BASKET API: {data.get('results',0)} partite trovate")
        data = data.get("response",[])
    except Exception as e:
        print(f"ERRORE BASKET: {e}")
        return []
    lista = []
    for f in data:
        try:
            home = f["teams"]["home"]["name"]; away = f["teams"]["away"]["name"]
            country = f["league"].get("country",""); league = f["league"]["name"]
            ora = f["fixture"]["date"][11:16]
            for book in f.get("bookmakers",[]):
                for bet in book.get("bets",[]):
                    bname = bet.get("name","").lower()
                    if ("1st quarter" in bname or "first quarter" in bname) and ("total" in bname or "points" in bname):
                        for v in bet.get("values",[]):
                            tipo = v["value"]; odd = float(v["odd"])
                            handicap = bet.get("handicap","") or v.get("handicap","") or ""
                            if not handicap and "over" in tipo.lower():
                                handicap = tipo.lower().replace("over","").strip()
                            if "over" in tipo.lower() and 1.28 <= odd <= 1.42: # allargato a 1.30-1.40
                                lista.append(f"• [{country}] {ora} {home} vs {away} - {league} - 1Q Totale {handicap} {tipo} @ {odd}")
        except: continue
    return sorted(list(set(lista)))

# MESSAGGIO DI AVVIO - SE NON TI ARRIVA QUESTO, IL TOKEN E' SBAGLIATO
send(f"BOT DAMI V13.8 FIX ON - {datetime.now().strftime('%H:%M')} - TEST OK")

inviate=set(); rosso=set(); fatto_10=False

while True:
    try:
        if not is_orario_attivo():
            print(f"Zzz {datetime.now().hour}:{datetime.now().minute}")
            time.sleep(600); continue

        now = datetime.now()
        if now.hour == 10 and now.minute < 10 and not fatto_10: # allargato a 10 min
            print("AVVIO LISTE 10:00")
            over, corner, schedina = get_liste_10()
            basket = get_basket_1Q()
            send(f"📋 *TUTTE OVER 1.5 OGGI ({len(over)})*\n\n" + ("\n".join(over[:90]) if over else "Nessuna"))
            time.sleep(2)
            send(f"🚩 *CORNER 6.5 OGGI ({len(corner)})*\n\n" + ("\n".join(corner[:90]) if corner else "Nessuna"))
            time.sleep(2)
            send(schedina)
            time.sleep(2)
            send(f"🏀 *BASKET 1Q TOTALE 1.30-1.40 OGGI ({len(basket)})*\n\n" + ("\n".join(basket[:90]) if basket else "Nessun basket trovato - controlla piano API"))
            fatto_10=True
        if now.hour == 11: fatto_10=False

        # ... IL TUO LOOP LIVE UGUALE ...
        live=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json().get("response", [])
        for m in live:
            # ... tutto uguale a prima ...
            pass

        time.sleep(60)
    except Exception as e:
        print(f"ERRORE LOOP: {e}"); time.sleep(60)
