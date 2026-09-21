
from flask import Flask
import threading, time, requests, os

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY") # mettila su Render in Environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

HEADERS = {"x-apisports-key": API_KEY}
partite_calde = {}

def manda(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
    except: pass
    print(msg)

def loop_bot():
    while True:
        try:
            live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS).json()
            for f in live['response']:
                casa = f['teams']['home']['name']
                ospite = f['teams']['away']['name']
                minuti = f['fixture']['status']['elapsed'] or 0
                risultato = f"{f['goals']['home']}-{f['goals']['away']}"
                fid = f['fixture']['id']
                if minuti==0: continue
                s = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEADERS).json()
                try:
                    tp = int(s['response'][0]['statistics'][4]['value'] or 0) + int(s['response'][1]['statistics'][4]['value'] or 0)
                    tt = int(s['response'][0]['statistics'][2]['value'] or 0) + int(s['response'][1]['statistics'][2]['value'] or 0)
                    rc = int(s['response'][0]['statistics'][10]['value'] or 0) + int(s['response'][1]['statistics'][10]['value'] or 0)
                except: continue

                if rc>0 and minuti<=70 and risultato=="0-0":
                    manda(f"🔴 ROSSO 0-0 al {minuti}'\n{casa} vs {ospite}")
                if tp>=5 and minuti<=60 and fid not in partite_calde:
                    partite_calde[fid]=f"CALDA {minuti}'"
                    manda(f"🔥 CALDA al {minuti}' {casa} vs {ospite} - 5 tiri porta TOTALI Ris:{risultato}")
                if tt<=3 and 60<=minuti<=62 and fid not in partite_calde:
                    partite_calde[fid]=f"MORTA {minuti}'"
                    manda(f"🥶 MORTA al {minuti}' {casa} vs {ospite} - solo {tt} tiri Ris:{risultato}")
                if fid in partite_calde and risultato!="0-0" and "GOL" not in partite_calde[fid]:
                    manda(f"⚽ GOL! {casa} vs {ospite} {risultato} al {minuti}' Era {partite_calde[fid]}")
                    partite_calde[fid]+=" GOL"
        except Exception as e:
            print(e)
        time.sleep(90)

@app.route("/")
def home():
    return "V42 LIVE - TUTTO DENTRO - Damiano bot attivo"

# Fa partire il bot in background
threading.Thread(target=loop_bot, daemon=True).start()
