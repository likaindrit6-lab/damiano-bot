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
    TARGET = 1.80

    for p in partite[:50]:
        if len(bolla_txt) >= 5: break
        if quota_tot >= TARGET: break

        fid = p["fixture"]["id"]
        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]
        lega = p["league"]["name"]
        nazione = p["league"]["country"]
        ora_utc = p["fixture"]["date"]
        dt = datetime.fromisoformat(ora_utc.replace("Z", "+00:00")).astimezone(ITALY)
        if dt.hour < 8: continue
        orario = dt.strftime("%H:%M")

        odds_data = get_odd(fid)
        if not odds_data: continue

        try:
            bets = odds_data[0]["bookmakers"][0]["bets"]
            best_pick = None

            for bet in bets:
                bet_name = bet["name"].lower()

                # CERCA OVER GOAL
                if "over/under" in bet_name or "goals" in bet_name or "goal" in bet_name:
                    for v in bet["values"]:
                        val = v["value"].lower()
                        q = float(v["odd"])
                        # Solo Over sicuri
                        if ("over 0.5" in val or "over 1.5" in val) and 1.08 <= q <= 1.35:
                            if best_pick is None or q < best_pick["quota"]:
                                best_pick = {"segno": val, "quota": q, "tipo": f"Over {val}"}

                # CERCA ESITO GOAL (GG)
                if "both teams to score" in bet_name or "btts" in bet_name:
                     for v in bet["values"]:
                        if "yes" in v["value"].lower():
                            q = float(v["odd"])
                            if 1.25 <= q <= 1.70 and quota_tot * q <= 1.90:
                                best_pick = {"segno": "GG", "quota": q, "tipo": "Goal (GG)"}

            # Se ha trovato un pick GOAL/OVER
            if best_pick:
                if quota_tot * best_pick["quota"] > 1.90: continue

                quota_tot *= best_pick["quota"]
                segno_show = best_pick["tipo"]
                bolla_txt.append(f"🕒 {orario} - [{nazione} - {lega}]\n{home} vs {away} -> {segno_show} @ {best_pick['quota']} ")
                bolla_save.append({"id": fid, "home": home, "away": away, "orario": orario, "segno": best_pick["segno"], "quota": best_pick["quota"], "segno_show": segno_show, "lega": lega, "nazione": nazione})

        except: continue

    if len(bolla_txt) < 2:
        return f"⚠️ Trovate solo {len(bolla_txt)} partite Over/Goal sicure oggi. Quota {quota_tot:.2f}. Riprovo più tardi quando ci sono più quote."

    with open(FILE_BOLLA, "w") as f:
        json.dump({"data": domani, "partite": bolla_save, "quota_tot": quota_tot}, f)

    testo = f"🎫 *BOLLA GOAL/OVER 90% - {domani}*\n*Quota Tot: {quota_tot:.2f} con {len(bolla_txt)} partite*\n\n"
    testo += "\n\n".join(bolla_txt)
    testo += f"\n\n💰 *Quota Totale: {quota_tot:.2f}*"
    return testo

def verifica_bolla():
    try:
        with open(FILE_BOLLA, "r") as f:
            data = json.load(f)
    except:
        return "Nessuna bolla salvata ancora"
    partite = data.get("partite", [])
    if not partite: return "Nessuna bolla da verificare"
    vinte = 0
    risultato_txt = f"📊 *VERIFICA BOLLA GOAL DEL {data.get('data')}*\nQuota: {data.get('quota_tot'):.2f}\n\n"
    for m in partite:
        res = get_fixture_result(m["id"])
        if not res:
            risultato_txt += f"⏳ {m['home']} vs {m['away']} - non giocata\n"
            continue
        status = res["fixture"]["status"]["short"]
        if status!= "FT":
            risultato_txt += f"⏳ {m['home']} vs {m['away']} - {status}\n"
            continue

        gol_home = res["goals"]["home"]
        gol_away = res["goals"]["away"]
        totale_gol = (gol_home or 0) + (gol_away or 0)
        gg = (gol_home or 0) > 0 and (gol_away or 0) > 0

        vinto = False
        if "over 0.5" in m["segno"].lower() and totale_gol >= 1: vinto = True
        if "over 1.5" in m["segno"].lower() and totale_gol >= 2: vinto = True
        if "gg" in m["segno"].lower() and gg: vinto = True
        if "over 2.5" in m["segno"].lower() and totale_gol >= 3: vinto = True

        if vinto:
            risultato_txt += f"✅ VINTO - {m['home']} {gol_home}-{gol_away} {m['away']} ({m['segno_show']} uscito!)\n"
            vinte += 1
        else:
            risultato_txt += f"❌ PERSO - {m['home']} {gol_home}-{gol_away} {m['away']} ({m['segno_show']} non uscito)\n"

    if vinte == len(partite):
        risultato_txt += f"\n🎉 *BOLLA GOAL VINTA!!! {vinte}/{len(partite)}* - Quota {data.get('quota_tot'):.2f}"
    else:
        risultato_txt += f"\n😭 *BOLLA PERSA* - {vinte}/{len(partite)} vinte"
    return risultato_txt

tg("✅ BOT V19 ONLINE - GOAL / OVER 90%")

last_check = ""
while True:
    now = datetime.now(ITALY)
    if now.hour == 10 and now.minute == 0:
        tg(crea_bolla())
        time.sleep(70)
    if now.hour == 0 and now.minute == 30 and last_check!= now.strftime("%Y-%m-%d"):
        last_check = now.strftime("%Y-%m-%d")
        tg("⏳ Controllo se la bolla GOAL di ieri ha vinto...")
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
                tg("⏳ Creo la bolla GOAL/OVER...")
                tg(crea_bolla())
                requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={upd_id+1}", timeout=10)
            elif "verifica" in text or "vinto" in text or "perso" in text or "risultato" in text:
                tg("⏳ Verifico il risultato GOAL...")
                tg(verifica_bolla())
                requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={upd_id+1}", timeout=10)
    except: pass
    time.sleep(30)
