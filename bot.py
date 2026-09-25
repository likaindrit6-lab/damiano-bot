import os, time, threading, requests
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "DAMI BOT V23 CALCIO LIVE"

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = (os.getenv("API_FOOTBALL_KEY") or "").strip()
HEAD = {"x-apisports-key": API}
BASE = "https://v3.football.api-sports.io"

def send(t):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=20)
        print(f"SEND {r.status_code}", flush=True)
    except Exception as e:
        print(f"SEND ERR {e}", flush=True)

def get_today_fixtures():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        resp = requests.get(f"{BASE}/fixtures?date={today}", headers=HEAD, timeout=20).json()
        return resp.get("response", [])
    except Exception as e:
        print(f"FIXT ERR {e}", flush=True)
        return []

def bot_loop():
    print("BOT LOOP PARTITO - CALCIO", flush=True)
    time.sleep(2)
    send(f"✅ BOT DAMI CALCIO ON - {datetime.now().strftime('%H:%M:%S')} - base VIVO attiva")

    # LISTA GIORNO - Manda subito qualcosa anche se sera
    fixtures = get_today_fixtures()
    print(f"Fixtures oggi: {len(fixtures)}", flush=True)
    
    lista = []
    for f in fixtures[:60]:
        try:
            ora = f["fixture"]["date"][11:16]
            home = f["teams"]["home"]["name"][:20]
            away = f["teams"]["away"]["name"][:20]
            lista.append(f"• {ora} {home} vs {away} - NO 0-0 | Over 1.5")
        except: continue
    
    if not lista:
        lista = ["• Nessuna partita rimasta stasera - lista completa domani alle 10:00"]

    send(f"📋 CALCIO OGGI - NO 0-0 ({len(lista)})\n\n" + "\n".join(lista[:45]))

    c = 0
    while True:
        try:
            c += 1
            print(f"VIVO {c} - {datetime.now().strftime('%H:%M:%S')} - fixtures:{len(fixtures)}", flush=True)
            
            # Ogni 10 minuti avviso che è vivo
            if c % 10 == 0:
                send(f"🔄 Bot calcio vivo {datetime.now().strftime('%H:%M:%S')} - controllo live attivo")

            # Alle 10:00 rimanda lista del giorno
            now = datetime.now()
            if now.hour == 10 and now.minute == 0:
                fixtures = get_today_fixtures()
                lista = []
                for f in fixtures[:80]:
                    try:
                        ora = f["fixture"]["date"][11:16]
                        home = f["teams"]["home"]["name"]
                        away = f["teams"]["away"]["name"]
                        lista.append(f"• {ora} {home} vs {away}")
                    except: continue
                if lista:
                    send(f"📋 LISTA 10:00 - {len(lista)} partite\n\n" + "\n".join(lista[:50]))
                time.sleep(61)

            time.sleep(60)
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
            time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
