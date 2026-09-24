import os, time, requests
from datetime import datetime

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}

print(f"TOKEN ok? {bool(TOKEN)} CHAT {CHAT} API ok? {bool(API)}")

def send(t):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t, "parse_mode":"Markdown"}, timeout=15)
        print(f"Inviato Telegram: {r.status_code}")
    except Exception as e:
        print(f"Errore send {e}")

def get_sot(fid):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=15).json()
        s = 0
        for tm in r.get("response", []):
            for st in tm.get("statistics", []):
                if st["type"] == "Shots on Goal":
                    s += st["value"] or 0
        return s
    except Exception:
        return 0

def get_avg(team_id):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEAD, timeout=15).json()
        tot = 0; c = 0
        for f in r.get("response", []):
            tot += f["goals"]["home"] + f["goals"]["away"]; c+=1
        return tot/c if c>0 else 0
    except Exception:
        return 0

def calcola_probabilita(sot, minute):
    base = sot * 18
    if minute >= 30: base += 10
    if minute >= 38: base += 8
    return min(93, max(12, int(base)))

send("✅ BOT DAMI V13.2 LIVE\nControllo ogni 60sec | Calda 4 tiri + % gol | Rosso attivo")

inviate = set()
rosso = set()
schedina_oggi = ""
ultimo_gg = 0

while True:
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        live_resp = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json()
        live = live_resp.get("response", [])
        print(f"{now.strftime('%H:%M:%S')} - Live trovate: {len(live)}")

        for m in live:
            try:
                fid = m["fixture"]["id"]
                minute = m["fixture"]["status"]["elapsed"] or 0
                home = m["teams"]["home"]["name"]
                away = m["teams"]["away"]["name"]
                country = m["league"]["country"]
                league = m["league"]["name"]
                gh = m["goals"]["home"]; ga = m["goals"]["away"]

                if fid not in rosso:
                    try:
                        ev = requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json()
                        for e in ev.get("response", []):
                            if e["type"] == "Card" and e["detail"] == "Red Card":
                                send(f"🟥 *ROSSO {minute}'*\n*{country} {league}*\n{home} vs {away} ({gh}-{ga})")
                                rosso.add(fid)
                    except Exception:
                        pass

                if fid in inviate: continue
                if minute == 0 or minute > 45: continue

                sot = get_sot(fid)
                prob = calcola_probabilita(sot, minute)

                if sot >= 4:
                    send(f"🔥 *CALDA {sot} TIRI {minute}'*\n*{country} {league}*\n{home} vs {away} ({gh}-{ga})\n⚽️ *Prob gol: {prob}% nei prox 15'*")
                    inviate.add(fid)
                elif sot <= 2 and minute >= 35 and sot > 0:
                    send(f"💀 *MORTA {sot} TIRI {minute}'*\n*{country} {league}*\n{home} vs {away}\n⚽️ *Prob gol: {prob}%*")
                    inviate.add(fid)

            except Exception as e:
                print(f"Err partita {e}")
                continue

        if now.hour == 10 and now.minute < 3 and schedina_oggi != today:
            # ... schedina come prima ...
            schedina_oggi = today

        if time.time() - ultimo_gg > 7200:
            # ... goal goal come prima ...
            ultimo_gg = time.time()

        time.sleep(60)
    except Exception as e:
        print(f"ERR LOOP {e}")
        time.sleep(60)
