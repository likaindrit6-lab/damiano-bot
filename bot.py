
import os, threading, time, requests, datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): 
    return "OK - Bot Live Full Schedine", 200

BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
FOOT=os.getenv("API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": FOOT}
BASE = "https://v3.football.api-sports.io"
inviati = set()

def tg(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", 
                      data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=15)
    except: pass

def get_live():
    try: return requests.get(f"{BASE}/fixtures?live=all", headers=HEADERS, timeout=15).json().get("response", [])
    except: return []

def get_fixtures_date(date_str):
    try:
        r = requests.get(f"{BASE}/fixtures?date={date_str}", headers=HEADERS, timeout=15).json()
        return r.get("response", [])
    except: return []

def get_stat(fixture_id, type_name):
    try:
        r = requests.get(f"{BASE}/fixtures/statistics?fixture={fixture_id}", headers=HEADERS, timeout=15).json()
        tot = 0
        for team_stat in r.get("response", []):
            for s in team_stat.get("statistics", []):
                if s["type"] == type_name and s["value"] is not None:
                    tot += int(s["value"])
        return tot
    except: return 0

def get_team_avg_goals(team_id):
    try:
        r = requests.get(f"{BASE}/fixtures?team={team_id}&last=5", headers=HEADERS, timeout=15).json()
        fixtures = r.get("response", [])
        if not fixtures: return 0
        goals = 0
        for f in fixtures:
            if f["teams"]["home"]["id"] == team_id:
                goals += f["goals"]["home"] or 0
            else:
                goals += f["goals"]["away"] or 0
        return goals / len(fixtures) if fixtures else 0
    except: return 0

def loop_live():
    tg("✅ BOT FINALE V2 ATTIVO\n🔥 CALDO=6 tiri 60'\n🧊 MORTA=2-3 att 60'\n🚩 CORNER=5 al 45'\n📋 Schedine MONTATE")
    while True:
        try:
            live = get_live()
            for f in live:
                fid = f["fixture"]["id"]
                minute = f["fixture"]["status"]["elapsed"] or 0
                gh, ga = f["goals"]["home"] or 0, f["goals"]["away"] or 0
                lega = f["league"]["name"]
                match_str = f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"

                if 40 <= minute <= 48:
                    k = f"corner_{fid}"
                    if k not in inviati:
                        c = get_stat(fid, "Corner Kicks")
                        if c >= 5:
                            tg(f"🚩 <b>5 CORNER al 45'</b>\n{match_str}\n🏆 {lega}\n{c} corner al {minute}'")
                            inviati.add(k)

                if 55 <= minute <= 70 and gh == 0 and ga == 0:
                    k1 = f"caldo_{fid}"
                    if k1 not in inviati:
                        tiri = get_stat(fid, "Total Shots")
                        if tiri >= 6:
                            tg(f"🔥 <b>CALDO</b>\n{match_str}\n🏆 {lega}\n0-0 al {minute}' - {tiri} tiri totali")
                            inviati.add(k1)
                    k2 = f"morta_{fid}"
                    if k2 not in inviati:
                        dang = get_stat(fid, "Dangerous Attacks") or get_stat(fid, "Attacks")
                        if 0 <= dang <= 3:
                            tg(f"🧊 <b>MORTA</b>\n{match_str}\n🏆 {lega}\n0-0 al {minute}' - solo {dang} attacchi")
                            inviati.add(k2)
            if len(inviati) > 500: inviati.clear()
        except Exception as e:
            print(e)
        time.sleep(180)

def schedina_facile_e_over():
    # Gira ogni giorno alle 10:05
    while True:
        now = datetime.datetime.now()
        if now.hour == 10 and 0 <= now.minute <= 10:
            try:
                domani = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                fixtures = get_fixtures_date(domani)
                
                # Filtro 1: Schedina facile 1.60/1.80 - prendo partite di Serie A, Premier, Bundesliga con squadre forti in casa
                facile = []
                over_grande = []
                
                for f in fixtures[:50]: # analizzo prime 50 per non consumare tutto
                    home_id = f["teams"]["home"]["id"]
                    away_id = f["teams"]["away"]["id"]
                    lega = f["league"]["name"]
                    match_str = f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"
                    
                    avg_home = get_team_avg_goals(home_id)
                    avg_away = get_team_avg_goals(away_id)
                    
                    # Per Over 1.5 grande: se entrambe nelle ultime 5 fanno media 2 gol
                    if avg_home >= 1.5 and avg_away >= 1.0:
                        over_grande.append(f"{match_str} ({lega}) - media {avg_home:.1f}/{avg_away:.1f}")
                    
                    # Per schedina facile: se in casa segna tanto
                    if avg_home >= 1.8 and len(facile) < 3:
                        facile.append(f"{match_str} ({lega})")
                    
                    time.sleep(0.5) # per non bruciare API

                if facile:
                    msg = "📋 <b>SCHEDINA FACILE ORE 10:00</b> - Quota 1.60/1.80\n\n"
                    msg += "\n".join([f"✅ {x} - 1" for x in facile[:3]])
                    msg += f"\n\nData: {domani}"
                    tg(msg)
                
                if over_grande:
                    msg2 = "📈 <b>SCHEDINA OVER 1.5 GRANDE</b> - Quota 3.50/4.00\nSquadre che nelle ultime 5 fanno 2 gol di media\n\n"
                    msg2 += "\n".join([f"⚽️ {x} - Over 1.5" for x in over_grande[:4]])
                    msg2 += f"\n\nData: {domani}"
                    tg(msg2)
                    
            except Exception as e:
                print(f"Errore schedina: {e}")
            
            time.sleep(3600*2) # dormi 2 ore dopo le 10
        time.sleep(300)

def gol_gol_loop():
    while True:
        try:
            oggi = datetime.datetime.now().strftime("%Y-%m-%d")
            fixtures = get_fixtures_date(oggi)
            picks = []
            for f in fixtures[:40]:
                home_id = f["teams"]["home"]["id"]
                away_id = f["teams"]["away"]["id"]
                # entrambe segnano spesso nelle ultime 5?
                ah = get_team_avg_goals(home_id)
                aa = get_team_avg_goals(away_id)
                if ah >= 1.0 and aa >= 1.0:
                    lega = f["league"]["name"]
                    picks.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} ({lega})")
                if len(picks) >= 3: break
                time.sleep(0.4)
            
            if picks:
                msg = "⚽️ <b>GOL GOL - 3 partite</b>\n\n" + "\n".join([f"🥅 {p} - Gol" for p in picks])
                tg(msg)
        except: pass
        time.sleep(7200) # ogni 2 ore

threading.Thread(target=loop_live, daemon=True).start()
threading.Thread(target=schedina_facile_e_over, daemon=True).start()
threading.Thread(target=gol_gol_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
