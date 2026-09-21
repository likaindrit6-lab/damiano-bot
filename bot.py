
from flask import Flask
import threading, time, requests, os

app = Flask(__name__)
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
HEADERS = {"x-apisports-key": API_KEY}
partite_calde = {}

def manda(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
    except: pass
    print(msg, flush=True)

def loop_bot():
    while True:
        try:
            live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS).json()
            for f in live.get('response',[]):
                casa=f['teams']['home']['name']; ospite=f['teams']['away']['name']
                minuti=f['fixture']['status']['elapsed'] or 0; risultato=f"{f['goals']['home']}-{f['goals']['away']}"; fid=f['fixture']['id']
                if minuti==0: continue
                s=requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEADERS).json()
                try:
                    tp=int(s['response'][0]['statistics'][4]['value'] or 0)+int(s['response'][1]['statistics'][4]['value'] or 0)
                    tt=int(s['response'][0]['statistics'][2]['value'] or 0)+int(s['response'][1]['statistics'][2]['value'] or 0)
                    rc=int(s['response'][0]['statistics'][10]['value'] or 0)+int(s['response'][1]['statistics'][10]['value'] or 0)
                except: continue
                if rc>0 and minuti<=70 and risultato=="0-0": manda(f"🔴 ROSSO 0-0 {minuti}' {casa} vs {ospite}")
                if tp>=5 and minuti<=60 and fid not in partite_calde:
                    partite_calde[fid]="CALDA"; manda(f"🔥 CALDA {minuti}' {casa} vs {ospite} 5 tiri porta TOTALI {risultato}")
                if tt<=3 and 60<=minuti<=62 and fid not in partite_calde:
                    partite_calde[fid]="MORTA"; manda(f"🥶 MORTA {minuti}' {casa} vs {ospite} solo {tt} tiri {risultato}")
                if fid in partite_calde and risultato!="0-0" and "GOL" not in partite_calde[fid]:
                    manda(f"⚽ GOL! {casa} {risultato} vs {ospite} al {minuti}' Era {partite_calde[fid]}"); partite_calde[fid]+=" GOL"
        except Exception as e: print(e)
        time.sleep(90)

@app.route("/")
def home(): return "V42 Damiano-bot LIVE - tutto dentro ok"

threading.Thread(target=loop_bot, daemon=True).start()
