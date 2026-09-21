
from flask import Flask
import threading, time, requests, os

app = Flask(__name__)
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
HEADERS = {"x-apisports-key": API_KEY}
partite_calde = {}
offset = 0

def manda(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
    except: pass
    print(msg, flush=True)

def handle_commands():
    global offset
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=20").json()
            for upd in r.get('result',[]):
                offset = upd['update_id']+1
                txt = upd.get('message',{}).get('text','')
                cid = upd.get('message',{}).get('chat',{}).get('id')
                if '/start' in txt:
                    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={cid}&text=✅ V42 CON MORTA LIVE! CHAT: {cid} Comandi: /schedina /live /gol")
                if '/live' in txt:
                    manda("🔍 Controllo live...")
        except: pass
        time.sleep(2)

def loop_bot():
    while True:
        try:
            live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS).json()
            print(f"Live trovate: {len(live.get('response',[]))}", flush=True)
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
                    partite_calde[fid]=f"CALDA"; manda(f"🔥 CALDA {minuti}' {casa} vs {ospite} 5 tiri porta Ris:{risultato}")
                if tt<=3 and 60<=minuti<=62 and fid not in partite_calde:
                    partite_calde[fid]=f"MORTA"; manda(f"🥶 MORTA {minuti}' {casa} vs {ospite} solo {tt} tiri Ris:{risultato}")
        except Exception as e: print(e, flush=True)
        time.sleep(90)

@app.route("/")
def home(): return "V42 LIVE OK"

threading.Thread(target=loop_bot, daemon=True).start()
threading.Thread(target=handle_commands, daemon=True).start()
