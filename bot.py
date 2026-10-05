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
    except:
        pass

def get_fixtures(date_str):
    try:
        r = requests.get(f"{BASE_URL}/fixtures?date={date_str}", headers=HEADERS, timeout=20).json()
        return r.get("response", [])
    except:
        return []

def get_odd(fid):
    try:
        r = requests.get(f"{BASE_URL}/odds?fixture={fid}", headers=HEADERS, timeout=20).json()
        return r.get("response", [])
    except:
        return []

def crea_bolla():
    now_italy = datetime.now(ITALY)
    OGGI = now_italy.strftime("%Y-%m-%d")
    partite = get_fixtures(OGGI)

    if not partite:
        return f"Niente partite oggi {OGGI}"

    bolla_txt = []
    bolla_save = []
    quota_tot = 1.0

    for p in sorted(partite, key=lambda x: x["fixture"]["date"])[:100]:
        if len(bolla_txt) >= 3:
            break
        if quota_tot >= 1.60:
            break

        fid = p["fixture"]["id"]
        dt = datetime.fromisoformat(p["fixture"]["date"].replace("Z", "+00:00")).astimezone(ITALY)

        if dt < now_italy:
            continue
        if dt.hour < 8:
            continue

        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]
        lega = p["league"]["name"]
        nazione = p["league"]["country"]
        orario = dt.strftime("%H:%M")

        odds = get_odd(fid)
        if not odds:
            continue

        try:
            bets = odds[0]["bookmakers"][0]["bets"]
            best = None
            for bet in bets:
                for v in bet["values"]:
                    try:
                        q = float(v["odd"])
                        if 1.05 <= q <= 1.25:
                            if best is None or q < best["q"]:
                                best = {"mercato": bet["name"], "scelta": v["value"], "q": q}
                    except:
                        continue

            if not best:
                continue
            if quota_tot * best["q"] > 1.70:
                continue

            quota_tot *= best["q"]
            txt = f"{best['mercato']} {best['scelta']}"
            bolla_txt.append(f"{orario} - {nazione} {lega}\n{home} vs {away}\n-> {txt} @ {best['q']}")
            bolla_save.append({"id": fid, "home": home, "away": away, "orario": orario, "quota": best["q"]})

        except:
            continue

    if len(bolla_txt) == 0:
        return f"Oggi {OGGI} dopo le {now_italy.strftime('%H:%M')} niente quotine basse"

    with open(FILE_BOLLA, "w") as f:
        json.dump({"data": OGGI, "partite": bolla_save, "quota_tot": quota_tot}, f)

    testo = f"BOLLA ODIERNA {OGGI}\nQuota Tot: {quota_tot:.2f} con {len(bolla_txt)} partite\n\n"
    testo += "\n\n".join(bolla_txt)
    testo += f"\n\nTotale: {quota_tot:.2f}"
    return testo

tg("BOT V23 ONLINE - FIXATO")

while True:
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1&timeout=10", timeout=15).json()
        if r.get("result"):
            last = r["result"][-1]
            text = last.get("message", {}).get("text", "").lower()
            uid = last["update_id"]
            if "bolla" in text:
                tg("Cerco 2-3 quotine basse odierne...")
                tg(crea_bolla())
                requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={uid+1}", timeout=10)
    except:
        pass
    time.sleep(20)
