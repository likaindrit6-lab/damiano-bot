import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V3 CLEAN - BANDIERE FIX"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=25)
        if r.status_code == 429:
            tg("TOKEN FINITO - pausa 1h")
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

def get_flag(paese):
    flags = {
        "Italy": "IT", "England": "UK", "Spain": "ES", "Germany": "DE",
        "France": "FR", "Portugal": "PT", "Netherlands": "NL",
        "Belgium": "BE", "Turkey": "TR", "Brazil": "BR", "Argentina": "AR",
        "USA": "US", "Japan": "JP", "Australia": "AU", "Mexico": "MX",
        "Colombia": "CO", "Chile": "CL", "Sweden": "SE", "Norway": "NO",
        "Denmark": "DK", "Poland": "PL", "Romania": "RO", "Greece": "GR",
        "Switzerland": "CH", "Austria": "AT", "Scotland": "UK", "World": "WORLD"
    }
    code = flags.get(paese, "FLAG")
    # mappa semplice senza emoji complesse
    emoji_map = {
        "IT": "\U0001f1ee\U0001f1f9", "UK": "\U0001f1ec\U0001f1e7", "ES": "\U0001f1ea\U0001f1f8",
        "DE": "\U0001f1e9\U0001f1ea", "FR": "\U0001f1eb\U0001f1f7", "PT": "\U0001f1f5\U0001f1f9",
        "NL": "\U0001f1f3\U0001f1f1", "BE": "\U0001f1e7\U0001f1ea", "TR": "\U0001f1f9\U0001f1f7",
        "BR": "\U0001f1e7\U0001f1f7", "AR": "\U0001f1e6\U0001f1f7", "US": "\U0001f1fa\U0001f1f8"
    }
    return emoji_map.get(code, code)

def invia_schedine_mattina():
    try:
        oggi = datetime.now(ITALY).strftime('%Y-%m-%d')
        fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
        if not fixtures or fixtures == "LIMIT": return
        lista = []
        for f in fixtures[:40]:
            ora = f['fixture']['date'][11:16]
            paese_en = f['league']['country']
            lega = f['league']['name']
            flag = get_flag(paese_en)
            lista.append(f"{flag} {paese_en.upper()} - {lega} | {ora} {f['teams']['home']['name']}-{f['teams']['away']['name']}")
        bomba = f"BOMBA 30 OVER 0.5 - {oggi}\n\n" + "\n\n".join([f"{i+1}. {x} -> Over 0.5" for i,x in enumerate(lista[:30])])
        tg(bomba)
        time.sleep(2)
        prog = f"PROGRESSIONE 1.80 - {oggi}\n\n" + "\n\n".join([f"- {x} -> Over 0.5" for x in lista[:7]]) + "\n\nQuota ~1.80"
        tg(prog)
    except Exception as e: print(f"ERR mattina {e}")

def scheduler_schedine():
    gia = ""
    while True:
        now = datetime.now(ITALY)
        oggi_str = now.strftime('%Y-%m-%d')
        if now.hour == 10 and now.minute < 10 and gia!= oggi_str:
            invia_schedine_mattina()
            gia = oggi_str
        time.sleep(300)

threading.Thread(target=scheduler_schedine, daemon=True).start()
time.sleep(2)
tg("BOT V3 CLEAN ATTIVO - FIX BANDIERE")

avvisati_gol, avvisati_squadra, preavvisati, preavvisati_1t, stats_cache = {}, set(), set(), set(), {}
ultimo_hb = 0

while True:
    try:
        now = datetime.now(ITALY)
        if 0 <= now.hour < 10:
            if now.hour == 0:
                avvisati_squadra.clear(); preavvisati.clear(); preavvisati_1t.clear(); avvisati_gol.clear(); stats_cache.clear()
            time.sleep(1800); continue

        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT": time.sleep(3600); continue
        if len(live) == 0: time.sleep(180); continue

        if time.time() - ultimo_hb > 7200:
            tg(f"VIVO - {len(live)} live - {now.strftime('%H:%M')}")
            ultimo_hb = time.time()

        for g in live:
            m = g["fixture"]["status"]["elapsed"]
            if m is None or m < 20 or m > 92: continue
            fid = g["fixture"]["id"]
            if fid in avvisati_squadra: continue
            home = g['teams']['home']['name']; away = g['teams']['away']['name']
            gh = g['goals']['home']; ga = g['goals']['away']
            paese_en = g['league']['country']; lega = g['league']['name']
            flag = get_flag(paese_en)
            prefisso = f"{flag} {paese_en.upper()} - {lega} |"
            sot_tot = stats_cache.get(fid, {}).get('sot', 0)

            if m >= 20:
                d = stats_cache.get(fid)
                if not d or time.time() - d.get('time',0) > 180:
                    st = api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
                    if st and len(st) >= 2:
                        sot = get_stat(st[0]['statistics'],'Shots on Goal') + get_stat(st[1]['statistics'],'Shots on Goal')
                        stats_cache[fid] = {'sot': sot, 'time': time.time()}
                        time.sleep(0.6)
                    sot_tot = stats_cache.get(fid, {}).get('sot',0)

            if 20 <= m <= 45 and fid not in preavvisati_1t and sot_tot >= 3:
                tg(f"1T {m}' {prefisso} TiriP:{sot_tot} {home} {gh}-{ga} {away}")
                preavvisati_1t.add(fid)
            if 45 <= m <= 69 and fid not in preavvisati and sot_tot >= 5:
                tg(f"PREPARATI {m}' {prefisso} TiriP:{sot_tot} {home} {gh}-{ga} {away}")
                preavvisati.add(fid)
            if 70 <= m <= 92 and sot_tot >= 6:
                squadra = home if gh <= ga else away
                perc = min(96, 70 + (m-45))
                tg(f"GIOCALO {m}' >{perc}% {prefisso} TiriP:{sot_tot} {home} {gh}-{ga} {away} NEXT {squadra}")
                avvisati_squadra.add(fid); avvisati_gol[fid] = gh+ga

        for g in live:
            fid = g["fixture"]["id"]
            if fid in avvisati_gol:
                tot = g["goals"]["home"] + g["goals"]["away"]
                if tot > avvisati_gol[fid]:
                    flag = get_flag(g['league']['country'])
                    tg(f"GOL VINTO! {flag} {g['league']['country']} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                    del avvisati_gol[fid]
        time.sleep(120)
    except Exception as e:
        print(f"ERR {e}", flush=True); time.sleep(30)
