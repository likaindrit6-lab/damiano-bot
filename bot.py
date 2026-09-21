import os, threading, time, requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
KEY = os.getenv("API_FOOTBALL_KEY")

# Memoria gol per non spammare
gol_gia_avvisati = set()

@app.route('/')
def home():
    return f"V12 SVEGLIO H24 - {datetime.now()} - BOT:{bool(BOT)} KEY:{bool(KEY)}"

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id":CHAT,"text":t}, timeout=15)
    except: pass

def keep_alive():
    # Questo lo tiene sveglio per sempre
    while True:
        try:
            # Si pinga da solo ogni 5 minuti
            port = os.getenv("PORT","10000")
            requests.get(f"http://localhost:{port}/", timeout=5)
        except: pass
        time.sleep(300) # 5 minuti

def monitor_partite():
    while True:
        try:
            headers = {"x-apisports-key": KEY}
            # Prende TUTTE le partite live di TUTTI i campionati
            url = "https://v3.football.api-sports.io/fixtures?live=all"
            r = requests.get(url, headers=headers, timeout=20).json()
            fixtures = r.get("response", [])
            
            if not fixtures:
                time.sleep(90)
                continue

            msg = f"🔴 LIVE ORA: {len(fixtures)} partite in tutto il mondo - {datetime.now().strftime('%H:%M')}\n\n"
            count = 0
            for f in fixtures:
                if count >= 30: break # max 30 per messaggio per non bannarti
                league = f['league']['name']
                home = f['teams']['home']['name']
                away = f['teams']['away']['name']
                gol_home = f['goals']['home']
                gol_away = f['goals']['away']
                minute = f['fixture']['status']['elapsed']
                status = f['fixture']['status']['short']
                
                # ID unico partita
                fid = f['fixture']['id']
                score = f"{gol_home}-{gol_away}"
                
                # Avvisa solo se cambia punteggio
                key_score = f"{fid}{score}"
                if key_score not in gol_gia_avvisati:
                    gol_gia_avvisati.add(key_score)
                    if len(gol_gia_avvisati) > 1: # non avvisare al primo giro
                        send(f"⚽ GOL LIVE!\n{league}\n{home} {gol_home}-{gol_away} {away}\nMinuto: {minute}' - {status}")

                msg += f"{minute}' {home} {gol_home}-{gol_away} {away} ({league})\n"
                count += 1
            
            # Manda riepilogo ogni 90 sec come volevi tu
            if count > 0:
                send(msg)

        except Exception as e:
            send(f"Errore API: {e}")
        
        time.sleep(90) # 90 secondi precisi

def polling():
    off=0
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{BOT}/getUpdates?offset={off}&timeout=30", timeout=35).json()
            for u in r.get("result",[]):
                off=u["update_id"]+1
                txt=u.get("message",{}).get("text","")
                if "/start" in txt:
                    send("V12 SVEGLIO H24 ATTIVO DAMI ✅\n\nOra monitoro TUTTI i campionati da solo.\nNon devi scrivermi nulla.\nIo ti avviso ogni 90 sec + ad ogni GOL LIVE.\nSono sempre sveglio.")
                if "/live" in txt:
                    send("Sto controllando... ti mando tra 5 sec")
        except: time.sleep(5)

# AVVIA TUTTO
threading.Thread(target=keep_alive, daemon=True).start()
threading.Thread(target=monitor_partite, daemon=True).start()
threading.Thread(target=polling, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
