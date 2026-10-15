import os, time, requests, threading, json
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT = os.getenv('BOT_TOKEN')
CHAT = os.getenv('CHAT_ID')
KEY = os.getenv('API_FOOTBALL_KEY')

ITALY = timezone(timedelta(hours=2))
is_paused = False
last_id = 0
last_bolla_hour = -1

LEAGUES = {
 'Serie A': 135,
 'Serie B': 136,
 'Inghilterra': 39,
 'Spagna': 140,
 'Germania': 78,
 'Francia': 61,
 'Olanda': 88,
 'Portogallo': 94,
 'Turchia': 203,
 'Belgio': 144
}

TOP = {
 'Italy': 135,
 'England': 39,
 'Spain': 140,
 'Germany': 78,
 'France': 61,
 'Netherlands': 88,
 'Portugal': 94,
 'Belgium': 144,
 'Turkey': 203,
 'Scotland': 179,
 'Austria': 218,
 'Switzerland': 207,
 'Denmark': 106,
 'Sweden': 113,
 'Norway': 103,
 'Poland': 106,
 'Czech Republic': 345,
 'Croatia': 210,
 'Serbia': 286,
 'Greece': 197,
 'Romania': 283,
 'Bulgaria': 172,
 'Hungary': 271,
 'Slovakia': 332,
 'Slovenia': 373,
 'Ireland': 344,
 'Wales': 110,
 'Finland': 244,
 'Iceland': 164,
 'Cyprus': 318,
 'Malta': 389,
 'Luxembourg': 261,
 'Belarus': 116
}

def bad_league(n):
 n = n.lower()
 return any(x in n for x in ['u19','u21','u23','women','youth'])

app = Flask(__name__)

@app.route('/')
def home():
 return 'BOT V43 FINAL OK', 200

TAST = json.dumps({
 "keyboard": [
  ["Serie A","Serie B","Inghilterra"],
  ["Spagna","Germania","Francia"],
  ["Olanda","Portogallo","Turchia"],
  ["DOPPIA 90%"],
  ["BOLLA EUROPA 33 NAZIONI"],
  ["STATUS"],
  ["ACCENDI","SPEGNI"]
 ],
 "resize_keyboard": True
})

def tg(m, cid=None, keys=False):
 try:
  cid = cid or CHAT
  if not cid or not BOT:
   return
  base = 'https://api.telegram.org/bot' + BOT
  pay = {}
  pay['chat_id'] = cid
  pay['text'] = m
  pay['parse_mode'] = 'HTML'
  if keys:
   pay['reply_markup'] = json.loads(TAST)
  requests.post(base + '/sendMessage', json=pay, timeout=20)
 except:
  pass

def api(url):
 try:
  if not KEY:
   return []
  r = requests.get(url, headers={'x-apisports-key': KEY}, timeout=30)
  if r.status_code == 429:
   return 'LIMIT'
  return r.json().get('response', [])
 except:
  return []

def get_dc(fid):
 try:
  url = 'https://v3.football.api-sports.io/odds?fixture=' + str(fid)
  data = api(url)
  if not data or data == 'LIMIT' or len(data) == 0:
   return None
  books = data[0].get('bookmakers', [])
  for book in books[:3]:
   for bet in book.get('bets', []):
    if 'Double Chance' not in bet.get('name',''):
     continue
    best = None
    best_odd = 10.0
    for v in bet.get('values', []):
     try:
      odd = float(v['odd'])
      if odd < best_odd:
       best_odd = odd
       best = v['value']
     except:
      continue
    if best:
     prob = int(100 / best_odd) if best_odd else 0
     if 'Home/Draw' in best:
      return f"1X @ {best_odd:.2f} ({prob}%)", prob
     if 'Draw/Away' in best:
      return f"X2 @ {best_odd:.2f} ({prob}%)", prob
     if 'Home/Away' in best:
      return f"12 @ {best_odd:.2f} ({prob}%)", prob
 except:
  pass
 return None

def get_today():
 today = datetime.now(ITALY).strftime('%Y-%m-%d')
 url = 'https://v3.football.api-sports.io/fixtures?date=' + today + '&timezone=Europe/Rome'
 return api(url)

def run_bolla(cid=None, auto=False):
 try:
  data = get_today()
  if not data or data == 'LIMIT':
   if not auto:
    tg('BOLLA: Limite API', cid, True)
   return
  sel = []
  if not auto:
   tg('Cerco BOLLA 33...', cid, True)
  for country in TOP:
   top_id = TOP[country]
   found = None
   for f in data:
    lid = f['league']['id']
    ctry = f['league']['country']
    lname = f['league']['name']
    st = f['fixture']['status']['short']
    if lid!= top_id:
     continue
    if ctry!= country:
     continue
    if bad_league(lname):
     continue
    if st!= 'NS':
     continue
    found = f
    break
   if not found:
    continue
   fid = found['fixture']['id']
   ora = found['fixture']['date'][11:16]
   home = found['teams']['home']['name']
   away = found['teams']['away']['name']
   res = get_dc(fid)
   dc = res[0] if res else "1X @ 1.25"
   if res:
    time.sleep(0.5)
   sel.append(f"{ora} {home} vs {away} -> {dc}")
   if len(sel) >= 33:
    break
  if not sel:
   if not auto:
    tg('Oggi nessuna TOP', cid, True)
   return
  out = ""
  n = 0
  for m in sel:
   n += 1
   out += f"{n}. {m}\n"
  tg(f"🌍 BOLLA {len(sel)} NAZIONI\n\n{out}", cid, True)
 except Exception as e:
  tg(f"Err bolla {e}", cid, True)

def run_doppia(cid=None, auto=False):
 try:
  data = get_today()
  if not data or data == 'LIMIT':
   return
  out = []
  if not auto:
   tg('Cerco DOPPIA 90%...', cid, True)
  for f in data:
   ctry = f['league']['country']
   lid = f['league']['id']
   lname = f['league']['name']
   st = f['fixture']['status']['short']
   if ctry not in TOP:
    continue
   if bad_league(lname):
    continue
   if st!= 'NS':
    continue
   if lid!= TOP.get(ctry):
    continue
   res = get_dc(f['fixture']['id'])
   if not res:
    continue
   txt = res[0]
   prob = res[1]
   if prob < 80:
    continue
   ora = f['fixture']['date'][11:16]
   home = f['teams']['home']['name']
   away = f['teams']['away']['name']
   out.append((prob, f"{ora} {home} vs {away} -> {txt}"))
   time.sleep(0.4)
  if not out:
   if not auto:
    tg('Nessuna DOPPIA 90%', cid, True)
   return
  out.sort(key=lambda x: x[0], reverse=True)
  msg = ""
  n = 0
  for p, m in out:
   n += 1
   msg += f"{n}. {m}\n"
  tg(f"💎 DOPPIA 90% {len(out)}\n\n{msg}", cid, True)
 except:
  pass

def media(lid, name):
 txt = name.upper() + "\n"
 txt += datetime.now(ITALY).strftime("%d/%m %H:%M") + "\n\n"
 teams = api(f'https://v3.football.api-sports.io/teams?league={lid}&season=2024')
 if not teams:
  return 'Errore API'
 for t in teams[:12]:
  tid = t['team']['id']
  tname = t['team']['name']
  last = api(f'https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024')
  if not last or last == 'LIMIT':
   time.sleep(0.5)
   continue
  gf = 0
  gs = 0
  tot = 0
  c = 0
  for p in last:
   gh = p['goals']['home']
   ga = p['goals']['away']
   if gh is None:
    continue
   is_home = p['teams']['home']['id'] == tid
   if is_home:
    gf += gh
    gs += ga
   else:
    gf += ga
    gs += gh
   tot += gh + ga
   c += 1
  if c == 0:
   continue
  txt += f"{tname}: {gf}F/{gs}S Diff {gf-gs:+} Med {tot/c:.2f}\n"
  time.sleep(0.3)
 return txt

def poll():
 global is_paused, last_id
 try:
  if BOT:
   u = 'https://api.telegram.org/bot' + BOT + '/deleteWebhook?drop_pending_updates=true'
   requests.get(u, timeout=10)
 except:
  pass
 while True:
  try:
   if not BOT:
    time.sleep(60)
    continue
   base = 'https://api.telegram.org/bot' + BOT
   url = base + f'/getUpdates?offset={last_id+1}&timeout=20'
   r = requests.get(url, timeout=30).json()
   if r.get('ok'):
    for u in r.get('result', []):
     last_id = u['update_id']
     msg = u.get('message', {})
     txt = (msg.get('text') or '').strip()
     low = txt.lower()
     cid = msg.get('chat', {}).get('id')
     if not txt:
      continue
     if 'spegni' in low:
      is_paused = True
      tg('PAUSA', cid, True)
     elif 'accendi' in low or '/start' in low:
      is_paused = False
      tg('V43 LIVE OK', cid, True)
     elif 'status' in low:
      now = datetime.now(ITALY).strftime("%H:%M")
      tg(f'STATUS V43 OK {now}', cid, True)
     elif 'doppia' in low:
      run_doppia(cid)
     elif 'bolla' in low:
      run_bolla(cid)
     else:
      for k in LEAGUES:
       if k.lower() == low:
        tg(media(LEAGUES[k], k), cid, True)
  except:
   pass
  time.sleep(2)

def live_loop():
 global last_bolla_hour
 tg('V43 FINAL LIVE - Sistemato', keys=True)
 while True:
  try:
   if is_paused:
    time.sleep(30)
    continue
   now = datetime.now(ITALY)
   h = now.hour
   m = now.minute
   if 2 <= h < 6:
    time.sleep(300)
    continue
   if h!= last_bolla_hour and m < 10:
    last_bolla_hour = h
    run_bolla(auto=True)
    time.sleep(3)
    run_doppia(auto=True)
   time.sleep(60)
  except:
   time.sleep(15)

threading.Thread(target=poll, daemon=True).start()
threading.Thread(target=live_loop, daemon=True).start()

if __name__ == '__main__':
 port = int(os.environ.get('PORT', 10000))
 app.run(host='0.0.0.0', port=port)
