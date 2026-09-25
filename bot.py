import os, time, requests
from datetime import datetime

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def get_stats(fid):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=15).json()
        sot=shots=dang=corners=0
        for tm in r.get("response", []):
            for st in tm.get("statistics", []):
                if st["type"]=="Shots on Goal": sot+=st["value"] or 0
                if st["type"]=="Total Shots": shots+=st["value"] or 0
                if st["type"] in ["Dangerous Attacks","Attacks"]: dang+=st["value"] or 0
                if st["type"]=="Corner Kicks": corners+=st["value"] or 0
        return sot, shots, dang, corners
    except: return 0,0,0,0

def get_corner_minuti(fid):
    try:
        ev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json()
        return [f"{e['time']['elapsed']}'" for e in ev.get("response",[]) if "Corner" in str(e.get("detail","")) or e["type"]=="Corner"]
    except: return []

def calcola_prob(sot, shots, dang, minute):
    prob = sot*12 + shots*2 + dang*0.7
    if minute >= 60: prob+=10
    if minute >= 75: prob+=12
    return min(94, max(10, int(prob)))

# --- NUOVA PARTE SCHEDINA 10:00 QUOTA 1.8 MEDIA 2.0 ---
def get_schedina():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        # Prende partite di oggi con quote
        fixtures = requests.get(f"https://v3.football.api-sports.io/odds?date={today}&bet=5", headers=HEAD, timeout=20).json().get("response",[])
        picks = []
        for f in fixtures:
            try:
                fixture = f["fixture"]["id"]
                league = f["league"]["name"]
                home = f["teams"]["home"]["name"]
                away = f["teams"]["away"]["name"]
                # Cerca Over 0.5 / Under
                for book in f.get("bookmakers",[]):
                    for bet in book.get("bets",[]):
                        if bet["id"]==5: # Goals Over/Under
                            for v in bet["values"]:
                                if "Over 1.5" in v["value"]:
                                    quota = float(v["odd"])
                                    if quota >= 1.80: # FILTRO QUOTA 1.8 CHE VOLEVI
                                        picks.append({"q": quota, "txt": f"{home} vs {away} - Over 1.5 @ {quota} ({league})"})
            except: continue
        
        if not picks: return None
        picks = sorted(picks, key=lambda x: x["q"])[:5] # Prende le 5 più basse sopra 1.8
        if len(picks) < 2: return None
        
        media = sum([p["q"] for p in picks]) / len(picks)
        if media < 2.0: return None # FILTRO MEDIA 2.0

        txt = f"📋 *SCHEDINA 10:00 - MEDIA {media:.2f}*\n\n"
        quota_tot = 1
        for p in picks:
            txt += f"• {p['txt']}\n"
            quota_tot *= p["q"]
        txt += f"\n*Quota Tot: {quota_tot:.2f}*"
        return txt
    except Exception as e:
        print(f"Errore schedina {e}")
        return None
# --- FINE SCHEDINA ---

send("BOT DAMI V13.5 COMPLETO RIPARTITO - CON SCHEDINA 1.8 / MEDIA 2.0")

inviate=set()
rosso=set()
schedina_inviata=False

while True:
    try:
        now = datetime.now()
        # SCHEDINA ALLE 10:00
        if now.hour == 10 and now.minute < 2 and not schedina_inviata:
            txt = get_schedina()
            if txt: send(txt)
            else: send("Schedina 10:00 - Oggi nessuna quota rispetta filtro 1.8 / media 2.0")
            schedina_inviata = True
        if now.hour == 11: schedina_inviata = False

        live=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json().get("response", [])
        for m in live:
            fid=m["fixture"]["id"]; minute=m["fixture"]["status"]["elapsed"] or 0
            if minute==0 or minute>90: continue
            home=m["teams"]["home"]["name"]; away=m["teams"]["away"]["name"]
            country=m["league"]["country"]; league=m["league"]["name"]
            gh=m["goals"]["home"]; ga=m["goals"]["away"]

            if fid not in rosso:
                try:
                    ev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json()
                    for e in ev.get("response", []):
                        if e["type"]=="Card" and e["detail"]=="Red Card":
                            send(f"🔴 *ROSSO {minute}'* {country} {league} {home} vs {away} ({gh}-{ga})"); rosso.add(fid)
                except: pass

            sot, shots, dang, corners = get_stats(fid)
            prob = calcola_prob(sot, shots, dang, minute)
            key = f"{fid}_{minute//15}"

            if prob >= 70 and key not in inviate and sot >=3:
                c_min = get_corner_minuti(fid); c_txt = f"Corner: {corners}"
                if c_min: c_txt += f" ({', '.join(c_min[-5:])})"
                send(f"⚽ *{minute}' {prob}% GOL* {country} {league} {home} vs {away} ({gh}-{ga}) Tiri: {sot} | Tot: {shots} | Att: {dang} | {c_txt}"); inviate.add(key)
            
            if minute <=45 and fid not in inviate:
                if sot>=4: send(f"🔥 *CALDA {sot} TIRI {minute}' - {prob}% GOL* {country} {league} {home} vs {away}"); inviate.add(fid)
                elif sot<=2 and minute>=35 and sot>0: send(f"🧊 *MORTA {sot} TIRI {minute}' - {prob}% GOL* {country} {league} {home} vs {away}"); inviate.add(fid)

        time.sleep(60)
    except Exception as e:
        print(e); time.sleep(60)
