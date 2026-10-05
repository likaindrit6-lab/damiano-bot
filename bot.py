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
    r = requests.get(f"{BASE_URL}/fixtures?date={date_str}", headers=HEADERS, timeout=20).json()
    return r.get("response", [])

def get_odd(fid):
    try:
        r = requests.get(f"{BASE_URL}/odds?fixture={fid}", headers=HEADERS, timeout=20).json()
        return r.get("response", [])
    except: return []

def trova_giocata_sicura(odds_data):
    sicure=[]
    try:
        bets=odds_data[0]["bookmakers"][0]["bets"]
        for bet in bets:
            for v in bet["values"]:
                try:
                    q=float(v["odd"])
                    if 1.05<=q<=1.35:
                        sicure.append({"mercato":bet["name"],"scelta":v["value"],"quota":q})
                except: continue
    except: pass
    sicure=sorted(sicure, key=lambda x:x["quota"])
    return sicure[0] if sicure else None

def crea_bolla():
    now_italy = datetime.now(ITALY)
    OGGI = now_italy.strftime("%Y-%m-%d") # <--- ODIERNA, non domani!
    partite = get_fixtures(OGGI)

    bolla_txt=[]; bolla_save=[]; quota_tot=1.0

    for p in sorted(partite, key=lambda x:x["fixture"]["date"])[:80]:
        if len(bolla_txt)>=5: break
        if quota_tot>=1.80: break

        fid=p["fixture"]["id"]
        dt=datetime.fromisoformat(p["fixture"]["date"].replace("Z","+00:00")).astimezone(ITALY)
        if dt < now_italy: continue # salta partite già iniziate oggi
        if dt.hour < 8: continue

        home=p["teams"]["home"]["name"]; away=p["teams"]["away"]["name"]
        lega=p["league"]["name"]; nazione=p["league"]["country"]
        orario=dt.strftime("%H:%M")

        odds=get_odd(fid)
        pick=trova_giocata_sicura(odds)
        if not pick: continue
        if quota_tot * pick["quota"] > 1.90: continue

        quota_tot*=pick["quota"]
        txt=f"{pick['mercato']} - {pick['scelta']}"
        bolla_txt.append(f"🕒 {orario} - [{nazione} - {lega}]\n{home} vs {away}\n-> {txt} @ {pick['quota']}")
        bolla_save.append({"id":fid,"home":home,"away":away,"orario":orario,"quota":pick["quota"],"scelta":txt})

    if len(bolla_txt)==0:
        return f"⚠️ Oggi {OG
