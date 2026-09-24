import os, time, requests
from datetime import datetime

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t, "parse_mode":"Markdown"}, timeout=15)
        print("Inviato")
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
        tot = 0
        c = 0
        for f in r.get("response", []):
            tot += f["goals"]["home"] + f["goals"]["away"]
            c += 1
        if c > 0:
            return tot / c
        return 0
    except Exception:
        return 0

def calcola_probabilita(sot, minute):
    # formula V14 semplice: più tiri + minuto avanzato = più probabile gol
    base = sot * 18
    if minute >= 30:
        base += 10
    if minute >= 38:
        base += 8
    # cap
    prob = min(93, max(12, int(base)))
    return prob

send("✅ BOT DAMI V13.1 - CON PROBABILITA'\nCalda 4 tiri + % gol | Morta 2 tiri | Rosso | Schedina 10:00 | Goal ogni 2h")

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

        for m in live:
            try:
                fid = m["fixture"]["id"]
                minute = m["fixture"]["status"]["elapsed"] or 0
                home = m["teams"]["home"]["name"]
                away = m["teams"]["away"]["name"]
                country = m["league"]["country"]
                league = m["league"]["name"]
                goals_home = m["goals"]["home"]
                goals_away = m["goals"]["away"]

                # ROSSO
                if fid not in rosso:
                    try:
                        ev_resp = requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json()
                        for e in ev_resp.get("response", []):
                            if e["type"] == "Card" and e["detail"] == "Red Card":
                                send(f"🟥 *ROSSO {minute}'*\n*{country} {league}*\n{home} vs {away} ({goals_home}-{goals_away})")
                                rosso.add(fid)
                    except Exception:
                        pass

                if fid in inviate:
                    continue
                if minute == 0 or minute > 45:
                    continue

                sot = get_sot(fid)
                prob = calcola_probabilita(sot, minute)

                if sot >= 4:
                    send(f"🔥 *CALDA {sot} TIRI {minute}'*\n*{country} {league}*\n{home} vs {away} ({goals_home}-{goals_away}) | Tiri: {sot}\n⚽️ *Prob gol 15min: {prob}%*")
                    inviate.add(fid)
                elif sot <= 2 and minute >= 35 and sot > 0:
                    send(f"💀 *MORTA {sot} TIRI {minute}'*\n*{country} {league}*\n{home} vs {away}\n⚽️ *Prob gol 15min: {prob}%*")
                    inviate.add(fid)

            except Exception as e:
                print(f"Err partita {e}")
                continue

        # SCHEDINA ORE 10:00 QUOTA 1.70-1.80
        if now.hour == 10 and now.minute < 3 and schedina_oggi != today:
            try:
                fx = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=20).json().get("response", [])[:15]
                txt = f"🎯 *SCHEDINA OGGI {today} - QUOTA 1.70/1.80*\n5-6 partite facili:\n\n"
                c = 0
                for f in fx:
                    if c >= 6:
                        break
                    avg_h = get_avg(f["teams"]["home"]["id"])
                    avg_a = get_avg(f["teams"]["away"]["id"])
                    avg = (avg_h + avg_a) / 2
                    if avg >= 1.8:
                        txt += f"• {f['league']['country']} {f['league']['name']}: {f['teams']['home']['name']}-{f['teams']['away']['name']} -> Over 0.5\n"
                        c += 1
                txt += "\nTotale ~1.75 quota API"
                send(txt)
                schedina_oggi = today
            except Exception as e:
                print(f"Err schedina {e}")

        # 3 PARTITE GOAL GOAL OGNI 2 ORE
        if time.time() - ultimo_gg > 7200:
            try:
                fx = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=20).json().get("response", [])[:30]
                best = []
                for f in fx:
                    if get_avg(f["teams"]["home"]["id"]) > 1.2 and get_avg(f["teams"]["away"]["id"]) > 1.2:
                        best.append(f)
                    if len(best) >= 3:
                        break
                if best:
                    txt = f"⚽️⚽️ *3 PARTITE GOAL GOAL - {now.strftime('%H:%M')}*\n\n"
                    for b in best:
                        txt += f"• *{b['league']['country']} {b['league']['name']}*\n  {b['teams']['home']['name']} vs {b['teams']['away']['name']} -> Goal\n\n"
                    send(txt)
                    ultimo_gg = time.time()
            except Exception as e:
                print(f"Err GG {e}")

        time.sleep(60)

    except Exception as e:
        print(f"ERR LOOP PRINCIPALE {e}")
        time.sleep(60)
