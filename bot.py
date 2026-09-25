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

# --- SOLO QUESTO AGGIUNTO - ORARIO 08:00 -> 02:00 ---
def is_orario_attivo():
    h = datetime.now().hour
    if h >= 8: return True   # 08:00 -> 23:59
    if h < 2: return True    # 00:00 -> 01:59
    return False             # 02:00 -> 07:59 DORME
# --- FINE ORARIO ---

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

def get_liste_10():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        odds_data = requests.get(f"https://v3.football.api-sports.io/odds?date={today}", headers=HEAD, timeout=25).json().get("response",[])
    except: return None, None, None
    lista_over15 = []
    lista_corner65 = []
    picks_sicuri = []
    for f in odds_data:
        try:
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            league = f["league"]["name"]
            ora = f["fixture"]["date"][11:16]
            nome = f"{ora} {home} vs {away} ({league})"
            for book in f.get("bookmakers",[]):
                for bet in book.get("bets",[]):
                    bname = bet.get("name","").lower()
                    bid = bet.get("id",0)
                    for v in bet.get("values",[]):
                        val = v["value"]; odd = float(v["odd"])
                        if bid==5 and "Over 1.5" in val and odd <= 1.40:
                            lista_over15.append(f"• {nome} @ {odd}")
                            if 1.05 <= odd <= 1.30:
                                picks_sicuri.append({"txt": f"{home} vs {away} Over 1.5 @ {odd}", "q": odd})
                        if "corner" in bname and "Over 6.5" in val and odd <= 1.60:
                            lista_corner65.append(f"• {nome} @ {odd}")
                        if bid==6 and "Over 6.5" in val and odd <= 1.60:
                             lista_corner65.append(f"• {nome} @ {odd}")
        except: continue
    lista_over15 = sorted(list(set(lista_over15)))
    lista_corner65 = sorted(list(set(lista_corner65)))
    picks_sicuri = sorted(list({p['txt']: p for p in picks_sicuri}.values()), key=lambda x: x['q'])
    schedina_txt = ""
    quota_tot = 1
    usate = []
    for p in picks_sicuri:
        quota_tot *= p["q"]
        usate.append(p)
        if quota_tot >= 1.80:
            break
    if usate and quota_tot >= 1.80:
        schedina_txt = f"🎯 *SCHEDINA 1.80 TOTALE - Quota {quota_tot:.2f}*\n\n"
        for u in usate:
            schedina_txt += f"• {u['txt']}\n"
    else:
        schedina_txt = "Schedina 1.80: non ci sono abbastanza partite sicure oggi sotto 1.30"
    return lista_over15, lista_corner65, schedina_txt

send("BOT DAMI V13.6 ON - ORARIO 08:00-02:00")

inviate=set()
rosso=set()
fatto_10=False

while True:
    try:
        # --- CONTROLLO ORARIO ---
        if not is_orario_attivo():
            print(f"Zzz dormo {datetime.now().hour}:{datetime.now().minute} - riparto alle 08:00")
            time.sleep(600)
            continue

        now = datetime.now()
        if now.hour == 10 and now.minute < 5 and not fatto_10:
            over, corner, schedina = get_liste_10()
            if over is not None:
                txt1 = f"📋 *TUTTE OVER 1.5 OGGI ({len(over)})*\n\n" + ("\n".join(over[:90]) if over else "Nessuna trovata")
                send(txt1)
                time.sleep(2)
                txt2 = f"🚩 *TUTTE OVER 6.5 CORNER OGGI ({len(corner)})*\n\n" + ("\n".join(corner[:90]) if corner else "Nessuna trovata")
                send(txt2)
                time.sleep(2)
                send(schedina)
            fatto_10 = True
        if now.hour == 11:
            fatto_10 = False

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
