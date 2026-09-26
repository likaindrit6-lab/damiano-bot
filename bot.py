import os, time, requests, threading
from flask import Flask
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

ITALY = pytz.timezone("Europe/Rome")
app = Flask(__name__)
@app.route('/')
def home(): return "ok"

def tg(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"}, timeout=20)
    except: pass

def api_get(url):
    try:
        r = requests.get(url, headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        j = r.json()
        if r.status_code == 429: return "LIMIT"
        if "errors" in j and j["errors"] and "limit" in str(j["errors"]).lower(): return "LIMIT"
        return j.get("response", [])
    except: return []

avvisati = set()
gol_memoria = {}
giorno_reset = datetime.now(ITALY).day
ultimo_top = time.time() - 3000
ultima_schedina = 0
ultimo_golgol = 0 # <--- NUOVO

# --- SCHEDINA LIVE 15-50' ---
def build_schedina(live_list):
    cand = []
    for g in live_list:
        m = g["fixture"]["status"]["elapsed"] or 0
        if not (15 <= m <= 50): continue
        gh = g["goals"]["home"]; ga = g["goals"]["away"]
        if abs(gh-ga) > 1: continue
        if gh + ga > 2: continue
        prob = 70 + (5 if m>=25 else 0) + (5 if m>=35 else 0) + (8 if gh==ga else 0) + (5 if gh+ga==0 else 0)
        quota = 1.28 if prob > 80 else 1.22
        cand.append((prob, quota, g))
    cand.sort(key=lambda x: x[0], reverse=True)
    return cand[:3]

# --- NUOVO: PALINSESTO GOL GOL ---
def build_gol_gol_prematch():
    oggi = datetime.now(ITALY).strftime("%Y-%m-%d")
    fixtures = api_get(f"https://v3.football.api-sports.io/fixtures?date={oggi}")
    if fixtures == "LIMIT" or not fixtures:
        return []

    # Leghe dove esce più GOL GOL
    leghe_gg = ["Eredivisie", "Bundesliga", "Jupiler", "Super Lig", "Championship", "Premier League", "Serie A", "La Liga", "Ligue 1"]

    candidati = []
    for f in fixtures:
        if f["fixture"]["status"]["short"]!= "NS": continue # solo non iniziate
        lega = f["league"]["name"]
        # dai priorità alle leghe da GG
        score_lega = 10 if any(x in lega for x in leghe_gg) else 0

        # prendi orario
        ora = datetime.fromtimestamp(f["fixture"]["timestamp"], ITALY).strftime("%H:%M")

        # prob base + bonus lega
        prob = 55 + score_lega
        # piccolo random per variare ogni 2 ore non è perfetto ma intanto va
        candidati.append((prob, ora, f))

    candidati.sort(key=lambda x: x[0], reverse=True)
    return candidati[:2] # le 2 migliori

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

while True:
    now_it = datetime.now(ITALY)
    if now_it.day!= giorno_reset:
        avvisati.clear(); gol_memoria.clear(); giorno_reset = now_it.day
        tg(f"🔄 Reset giorno {giorno_reset}")

    live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
    if live == "LIMIT":
        tg("⚠️ Limite API, pausa 1h"); time.sleep(3600); continue

    # === 1. PALINSESTO GOL GOL OGNI 2 ORE ===
    if time.time() - ultimo_golgol >= 7200: # 7200 = 2 ore
        picks = build_gol_gol_prematch()
        if picks:
            txt = f"⚽️ <b>PALINSESTO GOL GOL - {now_it.strftime('%H:%M')}</b>\nLe 2 più probabili di oggi\n\n"
            for prob, ora, ff in picks:
                txt += f"🕐 {ora} - {ff['league']['name']}\n{ff['teams']['home']['name']} vs {ff['teams']['away']['name']}\n👉 <b>GOL GOL SI</b> | {prob}%\n\n"
            tg(txt)
        ultimo_golgol = time.time()

    if not live:
        time.sleep(60); continue

    # === 2. LIVE DAL 55' + GOL ALERT ===
    for g in live:
        fid = g["fixture"]["id"]
        m = g["fixture"]["status"]["elapsed"] or 0
        gh = g["goals"]["home"]; ga = g["goals"]["away"]
        tot = gh + ga

        if fid in gol_memoria:
            if tot > gol_memoria[fid]:
                tg(f"⚽️ <b>GOL! {m}'</b>\n🌍 {g['league']['name']}\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}")
        gol_memoria[fid] = tot
        gol_memoria[f'{fid}_score'] = f"{gh}-{ga}"

        if m < 55 or m > 90: continue
        if fid in avvisati: continue
        if abs(gh-ga) >= 3: continue
        if gh + ga >= 5: continue

        perc = 80 + (2 if m>=60 else 0) + (3 if m>=65 else 0) + (4 if m>=70 else 0) + (3 if m>=75 else 0)
        if perc > 92: perc = 92
        tg(f"🔥 {m}' >80%\n🌍 {g['league']['country']} - {g['league']['name']}\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\n<b>Prob: {perc}%</b>")
        avvisati.add(fid)

    # === 3. TOP 3 OGNI ORA ===
    if time.time() - ultimo_top >= 3600:
        cand = []
        for g in live:
            m = g["fixture"]["status"]["elapsed"] or 0
            if m < 55 or m > 90: continue
            gh = g["goals"]["home"]; ga = g["goals"]["away"]
            if abs(gh-ga) >= 3: continue
            if gh + ga >= 5: continue
            p = 80 + (2 if m>=60 else 0) + (3 if m>=65 else 0) + (4 if m>=70 else 0) + (3 if m>=75 else 0)
            cand.append((p, g))
        cand.sort(key=lambda x: x[0], reverse=True)
        top = cand[:3]
        if top:
            txt = f"🔥 TOP 3 DAL 55' - {now_it.strftime('%H:%M')}\n\n"
            for p, gg in top:
                txt += f"⚽️ {gg['fixture']['status']['elapsed']}' 🌍 {gg['league']['country']} - {gg['league']['name']}\n{gg['teams']['home']['name']} {gg['goals']['home']}-{gg['goals']['away']} {gg['teams']['away']['name']}\n<b>Prob: {min(p,92)}%</b>\n\n"
            tg(txt)
        ultimo_top = time.time()

    # === 4. SCHEDINA LIVE OGNI ORA ===
    if time.time() - ultima_schedina >= 3600:
        picks = build_schedina(live)
        if len(picks) >= 2:
            quota_tot = 1.0; txt = f"🎫 SCHEDINA 1.50 LIVE - {now_it.strftime('%H:%M')}\nDal 15' al 50' - Prossimo Gol\n\n"
            for prob, q, gg in picks:
                quota_tot *= q; m = gg['fixture']['status']['elapsed']
                txt += f"⚽️ {m}' {gg['teams']['home']['name']} {gg['goals']['home']}-{gg['goals']['away']} {gg['teams']['away']['name']}\n👉 Prossimo Gol | {prob}% @ {q}\n🌍 {gg['league']['name']}\n\n"
                if quota_tot >= 1.50: break
            txt += f"💰 QUOTA TOT: {quota_tot:.2f}"
            if quota_tot >= 1.45: tg(txt)
        ultima_schedina = time.time()

    time.sleep(60)
