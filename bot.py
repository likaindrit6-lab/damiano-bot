import os
import time
import requests
import threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT OK - DAMI FINALE 00-10"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}, timeout=20)
    except Exception:
        pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        if r.status_code == 429:
            return "LIMIT"
        return r.json().get("response", [])
    except Exception:
        return []

def get_stat(arr, nome):
    for s in arr:
        if s.get('type') == nome:
            try:
                v = s.get('value')
                if v is None:
                    return 0
                return int(str(v).replace('%','').strip() or 0)
            except Exception:
                return 0
    return 0

def get_sot(fid):
    d = stats_cache.get(fid)
    if d:
        return d.get('sot', 0)
    return 0

time.sleep(2)
tg("✅ BOT ATTIVO - FIX DEFINITIVO - NANNA 00-10")

avvisati_gol = {}
avvisati_squadra = set()
preavvisati = set()
preavvisati_1t = set()
stats_cache = {}
ultimo_hb = 0

while True:
    try:
        now = datetime.now(ITALY)
        if 0 <= now.hour < 10:
            if now.hour == 0:
                avvisati_squadra.clear()
                preavvisati.clear()
                preavvisati_1t.clear()
                avvisati_gol.clear()
                stats_cache.clear()
            time.sleep(1800)
            continue

        if time.time() - ultimo_hb > 900:
            lc = api_get("https://v3.football.api-sports.io/fixtures?live=all")
            if lc == "LIMIT":
                time.sleep(3600)
                continue
            tg(f"✅ VIVO - {len(lc)} live - {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT":
            time.sleep(3600)
            continue
        if len(live) == 0:
            time.sleep(120)
            continue

        for g in live:
            m = g["fixture"]["status"]["elapsed"]
            if m is None:
                continue
            if m < 20 or m > 92:
                continue
            fid = g["fixture"]["id"]
            if fid in avvisati_squadra:
                continue
            home = g['teams']['home']['name']
            away = g['teams']['away']['name']
            gh = g['goals']['home']
            ga = g['goals']['away']
            d = stats_cache.get(fid)
            if not d or time.time() - d.get('time', 0) > 120:
                try:
                    st = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if st and len(st) >= 2:
                        sot = get_stat(st[0]['statistics'], 'Shots on Goal') + get_stat(st[1]['statistics'], 'Shots on Goal')
                        stats_cache[fid] = {'sot': sot, 'time': time.time()}
                        time.sleep(0.4)
                except Exception:
                    pass
            sot_tot = get_sot(fid)
            if 20 <= m <= 45 and fid not in preavvisati_1t:
                if sot_tot >= 3:
                    tg(f"⚽️ 1T {m}' TiriP:{sot_tot} {home} {gh}-{ga} {away}")
                    preavvisati_1t.add(fid)
            if 60 <= m <= 69 and fid not in preavvisati:
                if sot_tot >= 5:
                    perc = 70 + (m - 45)
                    if perc > 90:
                        perc = 90
                    tg(f"👀 PREPARATI {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away}")
                    preavvisati.add(fid)
            if 70 <= m <= 92:
                if sot_tot >= 6:
                    squadra = home if gh <= ga else away
                    perc = 70 + (m - 45)
                    if perc > 96:
                        perc = 96
                    tg(f"🔥 GIOCALO {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away} NEXT {squadra}")
                    avvisati_squadra.add(fid)
                    avvisati_gol[fid] = gh + ga

        for g in live:
            fid = g["fixture"]["id"]
            if fid in avvisati_gol:
                tot_goals = g["goals"]["home"] + g["goals"]["away"]
                if tot_goals > avvisati_gol[fid]:
                    tg(f"✅ GOL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                    del avvisati_gol[fid]

        time.sleep(120)

    except Exception as e:
        print(f"ERR {e}", flush=True)
        time.sleep(30)
