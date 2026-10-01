import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT OK V2 - 00-10 ANTI SPRECO"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        if r.status_code == 429:
            tg("⛔️ TOKEN FINITO - pausa 1h")
            return "LIMIT"
        return r.json().get("response", [])
    except: return []

def get_stat(arr, nome):
    for s in arr:
        if s.get('type') == nome:
            try:
                v = s.get('value')
                if v is None: return 0
                return int(str(v).replace('%','').strip() or 0)
            except: return 0
    return 0

time.sleep(2)
tg("✅ BOT V2 ANTI SPRECO - NANNA 00-10")

avvisati_gol, avvisati_squadra, preavvisati, preavvisati_1t, stats_cache = {}, set(), set(), set(), {}
ultimo_hb = 0

while True:
    try:
        now = datetime.now(ITALY)
        if 0 <= now.hour < 10: # NANNA MEZZANOTTE - 10
            if now.hour == 0:
                avvisati_squadra.clear(); preavvisati.clear(); preavvisati_1t.clear(); avvisati_gol.clear(); stats_cache.clear()
            time.sleep(1800)
            continue

        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT":
            time.sleep(3600); continue
        if len(live) == 0:
            time.sleep(180); continue

        if time.time() - ultimo_hb > 7200: # FIX: ORA OGNI 2 ORE NON OGNI 20 MIN
            tg(f"✅ VIVO - {len(live)} live - {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        for g in live:
            m = g["fixture"]["status"]["elapsed"]
            if m is None or m < 20 or m > 92: continue
            fid = g["fixture"]["id"]
            if fid in avvisati_squadra: continue
            home = g['teams']['home']['name']; away = g['teams']['away']['name']
            gh = g['goals']['home']; ga = g['goals']['away']

            sot_tot = stats_cache.get(fid, {}).get('sot', 0)

            if m >= 55:
                d = stats_cache.get(fid)
                if not d or time.time() - d.get('time',0) > 180:
                    st = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if st and len(st) >= 2:
                        sot = get_stat(st[0]['statistics'],'Shots on Goal') + get_stat(st[1]['statistics'],'Shots on Goal')
                        stats_cache[fid] = {'sot': sot, 'time': time.time()}
                        time.sleep(0.6)
                    sot_tot = stats_cache.get(fid, {}).get('sot',0)

            if 20 <= m <= 45 and fid not in preavvisati_1t and sot_tot >= 3:
                tg(f"⚽️ 1T {m}' TiriP:{sot_tot} {home} {gh}-{ga} {away}"); preavvisati_1t.add(fid)
            if 60 <= m <= 69 and fid not in preavvisati and sot_tot >= 5:
                tg(f"👀 PREPARATI {m}' TiriP:{sot_tot} {home} {gh}-{ga} {away}"); preavvisati.add(fid)
            if 70 <= m <= 92 and sot_tot >= 6:
                squadra = home if gh <= ga else away
                perc = min(96, 70 + (m-45))
                tg(f"🔥 GIOCALO {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away} NEXT {squadra}")
                avvisati_squadra.add(fid); avvisati_gol[fid] = gh+ga

        for g in live:
            fid = g["fixture"]["id"]
            if fid in avvisati_gol:
                tot = g["goals"]["home"] + g["goals"]["away"]
                if tot > avvisati_gol[fid]:
                    tg(f"✅ GOL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                    del avvisati_gol[fid]
        time.sleep(120) # FIX: 2 MIN PER ESSERE PIU REATTIVO
    except Exception as e:
        print(f"ERR {e}", flush=True); time.sleep(30)
