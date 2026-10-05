import os, time, requests, json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
ITALY = ZoneInfo("Europe/Rome")
FILE_BOLLA = "ultima_bolla.json"

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def get_fixtures(date_str):
    url = f"{BASE_URL}/fixtures?date={date_str}"
    r = requests.get(url, headers=HEADERS, timeout=20).json()
    return r.get("response", [])

def get_odd(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20).json()
        return r.get("response", [])
    except:
        return []

def get_fixture_result(fixture_id):
    url = f"{BASE_URL}/fixtures?id={fixture_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20).json()
        if r.get("response"):
            return r["response"][0]
    except: pass
    return None

def crea_bolla():
    domani = (datetime.now(ITALY) + timedelta(days=1)).strftime("%Y-%m-%d")
    partite = get_fixtures(domani)
    if not partite:
        return "⚠️ Poche partite domani, riprovo dopo"

    bolla_txt = []
    bolla_save = []
    quota_tot = 1.0

    for p in partite[:35]:
        fid = p["fixture"]["id"]
        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]
        ora_utc = p["fixture"]["date"]
        dt = datetime.fromisoformat(ora_utc.replace("Z", "+00:00")).astimezone(ITALY)
        orario = dt.strftime("%H:%M")

        odds_data = get_odd(fid)
        if not odds_data: continue
        try:
            book = odds_data[0]["bookmakers"][0]["bets"]
            for bet in book:
                if bet["name"] == "Match Winner":
                    vals = sorted(bet["values"], key=lambda x: float(x["odd"]))
                    q = float(vals[0]["odd"])
                    if 1.35 <= q <= 1.85:
                        segno_val = vals[0]["value"]
                        if segno_val == "Home": segno_show = f"1 ({home})"
                        elif segno_val == "Away": segno_show = f"2 ({away})"
                        else: segno_show = "X"

                        quota_tot *= q
                        bolla_txt.append(f"🕒 {orario} - {home} vs {away} -> {segno_show} @ {q}")
                        bolla_save.append({"id": fid, "home": home, "away": away, "orario": orario, "segno": segno_val, "quota": q, "segno_show": segno_show})
                        break
        except: continue
        if len(bolla_txt) >= 4: break

    if len(bolla_txt) < 2:
        return "⚠️ Oggi non ci sono abbastanza quote sicure"

    with open(FILE_BOLLA, "w") as f:
        json.dump({"data": domani, "partite": bolla_save, "quota_tot": quota_tot}, f)

    testo = f"🎫 *BOLLA DEL GIORNO - {domani}*\n*Quota Tot: {quota_tot:.2f}*\n\n"
    testo += "\n".join(bolla_txt)
    testo += f"\n\n💰 *Quota Totale: {quota_tot:.2f}*"
    testo += f"\nGioca 1.50€"
    return testo

def verifica_bolla():
    try:
        with open(FILE_BOLLA, "r") as f:
            data = json.load(f)
    except:
        return "Nessuna bolla salvata ancora"

    partite = data.get("partite", [])
    if not partite:
        return "Nessuna bolla da verificare"

    vinte = 0
    risultato_txt = f"📊 *VERIFICA BOLLA DEL {data.get('data')}*\nQuota: {data.get('quota_tot'):.2f}\n\n"

    for m in partite:
        res = get_fixture_result(m["id"])
        if not res:
            risultato_txt += f"⏳ {m['home']} vs {m['away']} - ancora non giocata\n"
            continue

        status = res["fixture"]["status"]["short"]
        if status!= "FT":
            risultato_txt += f"⏳ {m['home']} vs {m['away']} - {status} in corso/non finita\n"
            continue

        home_win = res["teams"]["home"]["winner"]
        away_win = res["teams"]["away"]["winner"]

        if home_win == True: vincente = "Home"
        elif away_win == True: vincente = "Away"
        else: vincente = "Draw"

        gol_home = res["goals"]["home"]
        gol_away = res["goals"]["away"]

        if vincente == m["segno"]:
            risultato_txt += f"✅ VINTO - {m['home']} {gol_home}-{gol_away} {m['away']} (avevi {m['segno_show']})\n"
            vinte += 1
        else:
            risultato_txt += f"❌ PERSO - {m['home']} {gol_home}-{gol_away} {m['away']} (avevi {m['segno_show']})\n"

    if vinte == len(partite):
        risultato_txt += f"\n🎉 *BOLLA VINTA!!!* 🎉\nHai preso {vinte}/{len(partite)} - Vinti {data.get('quota_tot')*1.5:.2f}€ con 1.50€"
    else:
        risultato_txt += f"\n😭 *BOLLA PERSA* - {vinte}/{len(partite)} vinte"

    return risultato_txt

# --- LOOP ---
tg("✅ BOT V15 ONLINE - Fixato senza pytz")

last_check = ""
while True:
    now = datetime.now(ITALY)

    if now.hour == 10 and now.minute == 0:
        tg(crea_bolla())
        time.sleep(70)

    if now.hour == 0 and now.minute == 30 and last_check!= now.strftime("%Y-%m-%d"):
        last_check = now.strftime("%Y-%m-%d")
        tg("⏳ Controllo se la bolla di ieri ha vinto...")
        time.sleep(5)
        tg(verifica_bolla())

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1&timeout=10"
        r = requests.get(url, timeout=15).json()
        if r.get("result"):
            last = r["result"][-1]
            text = last.get("message", {}).get("text", "").lower()
            upd_id = last["update_id"]

            if "bolla" in text:
                tg("⏳ Creo la bolla...")
                tg(crea_bolla())
                requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={upd_id+1}", timeout=10)
            elif "verifica" in text or "vinto" in text or "perso" in text or "risultato" in text:
                tg("⏳ Verifico il risultato...")
                tg(verifica_bolla())
                requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={upd_id+1}", timeout=10)
    except: pass

    time.sleep(30)
