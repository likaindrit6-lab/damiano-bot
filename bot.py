import os, time, requests, threading
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V5 DEFINITIVO - FINE 1T + 00-10"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

def tg(m):
    print(m, flush=True)
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}, timeout=25)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=30)
        if r.status_code == 429:
            tg("TOKEN FINITO - pausa 60 min")
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

def get_flag(p):
    m = {"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸","World":"🌍","Europe":"🇪🇺"}
    return m.get(p, f"[{p.upper()}]")

def invia_schedine_mattina():
    try:
        oggi = datetime.now(ITALY).strftime('%Y-%m-%d')
        fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
        if not fixtures or fixtures == "LIMIT": return
        lista = []
        for f in fixtures[:50]:
            ora = f['fixture']['date'][11:16]
            paese = f['league']['country']; lega = f['league']['name']
            flag = get_flag(paese)
            lista.append(f"{flag} {paese.upper()} - {lega} | {ora} {f['teams']['home']['name']}-{f['teams']['away']['name']}")
        if len(lista) >= 30:
            bomba = f"BOMBA 30 OVER 0.5 - {oggi}\n\n" + "\n\n".join([f"{i+1}. {x} -> Over 0.5" for i,x in enumerate(lista[:30])])
            tg(bomba); time.sleep(3)
        if len(lista) >= 7:
            prog = f"PROGRESSIONE 1.80 - {oggi}\n\n" + "\n\n".join([f"- {x} -> Over 0.5" for x in lista[:7]]) + "\n\nQuota ~1.80"
            tg(prog)
    except Exception as e: print(f"ERR mattina {e}")

def scheduler_giornaliero():
    gia_schedine = ""; gia_top3_ora = -1
    while True:
        try:
            now = datetime.now(ITALY)
            if now.hour == 10 and now.minute < 10 and gia_schedine!= now.strftime('%Y-%m-%d'):
                invia_schedine_mattina()
                gia_schedine = now.strftime('%Y-%m-%d')
            if now.hour >= 10 and now.minute < 10 and gia_top3_ora!= now.hour:
                live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
                if live and live!= "LIMIT" and len(live) > 0:
                    top = []
                    for g in live[:20]:
                        flag = get_flag(g['league']['country'])
                        top.append(f"{flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']} {g['fixture']['status']['elapsed']}'")
                    tg(f"TOP 3 LIVE ORA {now.strftime('%H:%M')}\n\n" + "\n".join(top[:3]))
                    gia_top3_ora = now.hour
        except: pass
        time.sleep(300)

threading.Thread(target=scheduler_giornaliero, daemon=True).start()
time.sleep(3)
tg("BOT V5 ATTIVO - FINE 1T + PAUSA 00-10 + GREEN GOAL")

avvisati_gol, avvisati_squadra, preavvisati, preav
