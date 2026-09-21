 
import os, time, threading, requests, datetime
from flask import Flask

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")

app = Flask(__name__)
CHAT_ID = None
memoria = {}
chiamate = 0
schedina_data = None

@app.route('/')
def home():
    return f"V10 90SEC - Chiamate {chiamate}/7200 - Live 0-0 monitorate - Chat {CHAT_ID}"

def send(text):
    if not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except: pass

def api(url):
    global chiamate
    try:
        r = requests.get(url, headers={"x-apisports-key": API_KEY}, timeout=20)
        chiamate += 1
        return r.json()
    except:
        return {"response": []}

def bot_loop():
    global CHAT_ID, memoria, schedina_data
    off = 0
    # Thread telegram
    def tg():
        global CHAT_ID
        o = 0
        while True:
            try:
                r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={o}&timeout=20", timeout=25).json()
                for u in r.get("result", []):
                    o = u["update_id"] + 1
                    chat = u.get("message", {}).get("chat", {}).get("id")
                    txt = u.get("message", {}).get("text", "")
                    if "/start" in txt and chat:
                        CHAT_ID = chat
                        send(f"🔥 V10 ATTIVO 90 SEC!\nChat {chat} salvata\n\nSistema:\n90 sec x 10 partite 0-0\n⚠️ 0.5 PRIMA (3-7 tiri)\n🔥 CALDA 6+ tiri\n💀 MORTA\n🟥 ROSSO\nChiamate: {chiamate}/7200")
            except: time.sleep(5)
    threading.Thread(target=tg, daemon=True).start()

    while True:
        try:
            now = datetime.datetime.now()
            # schedina 10:00
            if now.hour == 10 and now.minute < 5 and schedina_data!= now.date():
                schedina_data = now.date()
                send("🎟️ SCHEDINA 10:00 - Controllo partite di oggi... (funzione in arrivo)")

            if chiamate > 7000:
                send(f"⚠️ 7000 chiamate raggiunte, pausa 1h")
                time.sleep(3600)
                chiamate = 0

            data = api("https://v3.football.api-sports.io/fixtures?live=all")
            lives = data.get("response", [])
            live00 = [f for f in lives if f["goals"]["home"]==0 and f["goals"]["away"]==0 and (f["fixture"]["status"]["elapsed"] or 0) >= 20]
            # Prendi le 10 più avanzate
            live00 = sorted(live00, key=lambda x: x["fixture"]["status"]["elapsed"] or 0, reverse=True)[:10]

            print(f"[{now.strftime('%H:%M:%S')}] LIVE 0-0: {len(live00)}/{len(lives)} | Chiamate {chiamate}")

            for f in live00:
                try:
                    fid = f["fixture"]["id"]
                    el = f["fixture"]["status"]["elapsed"] or 0
                    if el < 25 or el > 90: continue
                    home = f["teams"]["home"]["name"]; away = f["teams"]["away"]["name"]
                    league = f["league"]["name"]

                    old = memoria.get(fid, {"tiri":0,"prima":False,"calda":False,"morta":False})

                    sd = api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    tiri = 0; dang = 0; rosso=False
                    for ts in sd.get("response", []):
                        for s in ts["statistics"]:
                            if s["type"]=="Shots on Goal": tiri += s["value"] or 0
                            if s["type"]=="Dangerous Attacks": dang += s["value"] or 0
                            if s["type"]=="Red Cards" and (s["value"] or 0) > 0: rosso=True

                    # PRIMA
                    if not old["prima"] and tiri > old["tiri"] and 3 <= tiri <= 7 and dang > 20 and el >= 28 and el <= 75:
                        send(f"⚠️ SEGNALE 0.5 ({el}')\n{home} - {away}\n{league}\nTiri {old['tiri']}->{tiri} Att.per {dang}\n👉 ENTRA 0.5 PT / OVER 0.5")
                        old["prima"]=True
                    # CALDA
                    if not old["calda"] and el <= 65 and tiri >= 6 and tiri > old["tiri"]:
                        send(f"🔥 CALDA ({el}')\n{home} - {away}\nTiri {tiri} STA SPINGENDO FORTE!\n{league}")
                        old["calda"]=True
                    # ROSSO
                    if rosso:
                        send(f"🟥 ROSSO ({el}')\n{home} - {away}\nPartita con rosso - occhio gol!")
                    # MORTA
                    if not old["morta"] and el >= 65 and tiri <= 2:
                        send(f"💀 MORTA ({el}')\n{home} - {away}\nTiri {tiri} - partita morta, lascia stare")
                        old["morta"]=True

                    old["tiri"]=tiri
                    memoria[fid]=old
                    time.sleep(0.5)
                except: continue

            time.sleep(90)
        except Exception as e:
            print(f"ERR main {e}")
            time.sleep(30)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    print("V10 START")
    threading.Thread(target=run_flask, daemon=True).start()
    bot_loop()
