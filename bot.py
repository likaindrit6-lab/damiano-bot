
import os, threading, time, requests, datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): 
    return "OK - Bot Live - Full Logic", 200

BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
FOOT=os.getenv("API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": FOOT}
BASE = "https://v3.football.api-sports.io"

inviati = set()

def tg(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", 
                      data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=15)
    except: pass

def get_live():
    try:
        r = requests.get(f"{BASE}/fixtures?live=all", headers=HEADERS, timeout=15).json()
        return r.get("response", [])
    except: return []

def get_stat(fixture_id, type_name):
    try:
        r = requests.get(f"{BASE}/fixtures/statistics?fixture={fixture_id}", headers=HEADERS, timeout=15).json()
        tot = 0
        for team_stat in r.get("response", []):
            for s in team_stat.get("statistics", []):
                if s["type"] == type_name and s["value"] is not None:
                    tot += int(s["value"])
        return tot
    except: return 0

def loop():
    tg("✅ BOT FINALE ATTIVO\n🔥 CALDO=6 tiri 60'\n🧊 MORTA=2-3 attacchi 60'\n🚩 CORNER=5 al 45'\n📋 Schedine attive")
    
    while True:
        try:
            print("VIVO - controllo live...", flush=True)
            live = get_live()
            
            for f in live:
                fid = f["fixture"]["id"]
                minute = f["fixture"]["status"]["elapsed"] or 0
                gol_home = f["goals"]["home"] or 0
                gol_away = f["goals"]["away"] or 0
                lega = f["league"]["name"]
                home = f["teams"]["home"]["name"]
                away = f["teams"]["away"]["name"]
                match_str = f"{home} vs {away}"

                # --- 1. CORNER 40-48' ---
                if 40 <= minute <= 48:
                    key = f"corner_{fid}"
                    if key not in inviati:
                        corners = get_stat(fid, "Corner Kicks")
                        if corners >= 5:
                            tg(f"🚩 <b>5 CORNER</b>\n{match_str}\n🏆 {lega}\n{corners} corner al {minute}'")
                            inviati.add(key)

                # --- 2 & 3. CALDO / MORTA 55-70' ---
                if 55 <= minute <= 70 and gol_home == 0 and gol_away == 0:
                    # CALDO
                    key_c = f"caldo_{fid}"
                    if key_c not in inviati:
                        tiri = get_stat(fid, "Total Shots")
                        if tiri >= 6:
                            tg(f"🔥 <b>CALDO</b>\n{match_str}\n🏆 {lega}\n0-0 al {minute}' - {tiri} tiri")
                            inviati.add(key_c)
                    
                    # MORTA
                    key_m = f"morta_{fid}"
                    if key_m not in inviati:
                        dang = get_stat(fid, "Dangerous Attacks")
                        if dang == 0:
                            dang = get_stat(fid, "Attacks") # fallback
                        if 0 <= dang <= 3:
                            tg(f"🧊 <b>MORTA</b>\n{match_str}\n🏆 {lega}\n0-0 al {minute}' - solo {dang} attacchi")
                            inviati.add(key_m)

            # Pulizia cache ogni giorno
            if len(inviati) > 500:
                inviati.clear()

        except Exception as e:
            print(f"Errore loop: {e}", flush=True)

        # Controllo ogni 3 minuti - con 7200 al giorno sei largo
        time.sleep(180)

# Logica Schedine (semplificata per ora - poi la potenziamo)
def schedine_loop():
    while True:
        now = datetime.datetime.now()
        # Schedina facile ore 10:00
        if now.hour == 10 and now.minute < 5:
            tg("📋 <b>SCHEDINA FACILE ORE 10:00</b>\nPronta! (logica da potenziare domani con analisi ultime 5)")
            time.sleep(3600) # evita di rimandarla
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()
threading.Thread(target=schedine_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
