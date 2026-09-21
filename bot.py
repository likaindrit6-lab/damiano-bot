
import os, threading, time, requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": KEY}

calde = set()
morte = set()
rossi = set()
punteggi = {}

@app.route('/')
def home(): return f"V14 SVEGLIO PER SEMPRE ATTIVO {datetime.now()}"

def send(t):
 try:
  requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id":CHAT,"text":t}, timeout=15)
 except: pass

def get_stats(fid):
 try:
  r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEADERS, timeout=12).json()
  return r.get("response",[])
 except: return []

def get_events(fid):
 try:
  r = requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEADERS, timeout=12).json()
  return r.get("response",[])
 except: return []

def monitor():
 while True:
  try:
   live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS, timeout=20).json().get("response",[])
   for f in live:
    fid = f['fixture']['id']
    minute = f['fixture']['status']['elapsed'] or 0
    gh = f['goals']['home'] or 0
    ga = f['goals']['away'] or 0
    home = f['teams']['home']['name']
    away = f['teams']['away']['name']
    league = f['league']['name']
    score = f"{gh}-{ga}"

    if fid in punteggi and punteggi[fid]!= score and fid in calde:
     chi = home if gh > int(punteggi[fid].split('-')[0]) else away
     send(f"✅ HA SEGNATO DAMI!\n{league}\n{home} {gh}-{ga} {away} {minute}'\nGOL: {chi}")
    punteggi[fid] = score

    if minute < 45 or (gh+ga) > 2: continue

    stats = get_stats(fid)
    if len(stats)!=2:
     time.sleep(1)
     continue

    def gv(i,k):
     for s in stats[i]['statistics']:
      if k.lower() in s['type'].lower(): return int(s['value'] or 0)
     return 0

    sot = gv(0,"on Goal") + gv(1,"on Goal")
    tot = gv(0,"Total Shots") + gv(1,"Total Shots")
    dang = gv(0,"Dangerous") + gv(1,"Dangerous")
    corners = gv(0,"Corner") + gv(1,"Corner")

    if minute <= 60 and fid not in rossi:
     ev = get_events(fid)
     for e in ev:
      if e['type']=='Card' and 'Red' in e['detail']:
       rossi.add(fid)
       send(f"🟥 ROSSO ENTRO 60' DAMI!\n{league}\n{home} {gh}-{ga} {away} {e['time']['elapsed']}'\n{e['player']['name']}")

    if 45 <= minute <= 75 and fid not in calde:
     if sot >= 6 or (tot >= 12 and dang >= 60):
      calde.add(fid)
      fav = home if gv(0,"on Goal") >= gv(1,"on Goal") else away
      send(f"🔥 PARTITA CALDA DAMI {minute}'\n{league}\n{home} {gh}-{ga} {away}\nTiri porta:{sot} Tot:{tot} Dang:{dang} Corner:{corners}\nSta spingendo: {fav}\nOVER / NEXT GOAL")

    if 55 <= minute <= 80 and fid not in morte:
     if tot <= 6 and sot <= 3:
      morte.add(fid)
      send(f"🧊 PARTITA MORTA DA UNDER DAMI {minute}'\n{league}\n{home} {gh}-{ga} {away}\nTiri porta:{sot} Tot:{tot}\nUNDER 2.5")

    time.sleep(1.5)
  except: pass
  time.sleep(90)

def polling():
 off=0
 while True:
  try:
   r=requests.get(f"https://api.telegram.org/bot{BOT}/getUpdates?offset={off}&timeout=30", timeout=35).json()
   for u in r.get("result",[]):
    off=u["update_id"]+1
    if "/start" in u.get("message",{}).get("text",""):
     send("V14 ATTIVO E SVEGLIO PER SEMPRE DAMI ✅\nControllo ogni 90 sec tutte le partite.\nNon dormo più mai.")
  except: time.sleep(5)

def keep_alive():
 while True:
  try:
   port=os.getenv("PORT","10000")
   requests.get(f"http://localhost:{port}/", timeout=5)
  except: pass
  time.sleep(300)

threading.Thread(target=monitor, daemon=True).start()
threading.Thread(target=polling, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

if __name__=="__main__":
 app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
