
import os, time, requests
from datetime import datetime

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t, "parse_mode": "Markdown"}, timeout=20)
    except Exception as e:
        print("send error", e)

def is_orario_attivo():
    h = datetime.now().hour
    return h >= 8 or h < 2

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

def calcola_prob(sot, shots, dang, minute):
    prob = sot*12 + shots*2 + dang*0.7
    if minute >= 60: prob+=10
    if minute >= 75: prob+=12
    return min(94, max(10, int(prob)))

def get_liste_10():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        odds_data = requests.get(f"https://v3.football.api-sports.io/odds?date={today}", headers=HEAD, timeout=25).json().get("response",[])
    except: return [], [], "Errore liste"
    lista_over = []; lista_corner = []; picks = []
    for f in odds_data:
        try:
            home = f["teams"]["home"]["name"]; away = f["teams"]["away"]["name"]
            league = f["league"]["name"]; ora = f["fixture"]["date"][11:16]
            nome = f"{ora} {home} vs {away} ({league})"
            for book in f.get("bookmakers",[]):
                for bet in book.get("bets",[]):
                    bname = bet.get("name","").lower()
                    bid = bet.get("id",0)
                    for v in bet.get("values",[]):
                        try:
                            odd = float(v["odd"]); val = v["value"]
                            if bid==5 and "Over 1.5" in val and odd <= 1.40:
                                lista_over.append(f"• {nome} @ {odd}")
                                if 1.05 <= odd <= 1.30: picks.append({"txt": f"{home} vs {away} Over 1.5 @ {odd}", "q": odd})
                            if "corner" in bname and "Over 6.5" in val and odd <= 1.60:
                                lista_corner.append(f"• {nome} @ {odd}")
                        except: continue
        except: continue
    lista_over = sorted(list(set(lista_over)))
    lista_corner = sorted(list(set(lista_corner)))
    picks = sorted(list({p['txt']: p for p in picks}.values()), key=lambda x: x['q'])
    quota_tot = 1; usate = []
    for p in picks:
        quota_tot *= p["q"]; usate.append(p)
        if quota_tot >= 1.80: break
    if usate and quota_tot >= 1.80:
        schedina = f"🎯 SCHEDINA 1.80 - Quota {quota_tot:.2f}\n\n"
        for u in usate: schedina += f"• {u['txt']}\n"
    else:
        schedina = "Schedina 1.80: poche partite sicure oggi"
    return lista_over, lista_corner, schedina

def get_basket_1Q():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        data = requests.get(f"https://v3.basketball.api-sports.io/odds?date={today}", headers=HEAD, timeout=25).json().get("response",[])
    except Exception as e:
        print("basket error", e)
        return []
    lista = []
    for f in data:
        try:
            home = f["teams"]["home"]["name"]; away = f["teams"]["away"]["name"]
            country = f["league"].get("country",""); league = f["league"]["name"]; ora = f["fixture"]["date"][11:16]
            totale_inizio = ""; hnd_txt = ""; hnd_q = 0; q1_txt = ""
            for book in f.get("bookmakers",[]):
                for bet in book.get("bets",[]):
                    bname = bet.get("name","").lower()
                    if "quarter" in bname:
                        if ("1st quarter" in bname or "first quarter" in bname) and "total" in bname:
                            for v in bet.get("values",[]):
                                if "over" in v["value"].lower():
                                    try:
                                        odd = float(v["odd"])
                                        tv = float(bet.get("handicap") or 0)
                                        if 30 <= tv <= 48.5 and 1.25 <= odd <= 1.40:
                                            q1_txt = f"1Q Over {tv} @ {odd}"
                                    except: continue
                    else:
                        if "handicap" in bname and not hnd_txt:
                            for v in bet.get("values",[]):
                                try:
                                    odd = float(v["odd"])
                                    if 1.30 <= odd <= 1.40:
                                        hnd_txt = v["value"]; hnd_q = odd
                                except: continue
                        if "total" in bname and not totale_inizio:
                            for v in bet.get("values",[]):
                                if "over" in v["value"].lower():
                                    totale_inizio = str(bet.get("handicap") or "")
                                    break
            if hnd_txt and q1_txt:
                lista.append(f"• [{country}] {ora} {home} vs {away} - {league} - Hnd {hnd_txt} @ {hnd_q} / Tot {totale_inizio} / {q1_txt}")
        except: continue
    return sorted(list(set(lista)))

send("BOT DAMI V17 ON - RIPARATO ✅")

inviate=set(); rosso=set(); fatto_10=False

while True:
    try:
        if not is_orario_attivo():
            time.sleep(300); continue
        now = datetime.now()
        if not fatto_10:
            over, corner, schedina = get_liste_10()
            basket = get_basket_1Q()
            send(f"📋 OVER 1.5 OGGI ({len(over)})\n\n" + ("\n".join(over[:80]) if over else "Nessuna"))
            time.sleep(1)
            send(f"🚩 CORNER 6.5 OGGI ({len(corner)})\n\n" + ("\n".join(corner[:80]) if corner else "Nessuna"))
            time.sleep(1)
            send(schedina)
            time.sleep(1)
            send(f"🏀 BASKET HND 1.30-1.40 + 1Q ({len(basket)})\n\n" + ("\n".join(basket[:80]) if basket else "Nessun basket oggi"))
            fatto_10 = True

        if now.hour == 11: fatto_10 = False

        live=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json().get("response", [])
        for m in live:
            fid=m["fixture"]["id"]; minute=m["fixture"]["status"]["elapsed"] or 0
            if minute==0 or minute>90: continue
            home=m["teams"]["home"]["name"]; away=m["teams"]["away"]["name"]
            country=m["league"]["country"]; league=m["league"]["name"]
            gh=m["goals"]["home"]; ga=m["goals"]["away"]
            sot, shots, dang, corners = get_stats(fid)
            prob = calcola_prob(sot, shots, dang, minute)
            key = f"{fid}_{minute//15}"
            if prob >= 70 and key not in inviate and sot >=3:
                send(f"⚽ {minute}' {prob}% GOL {country} {league} {home} vs {away} ({gh}-{ga}) Tiri:{sot} Tot:{shots} Att:{dang} Corn:{corners}")
                inviate.add(key)
        time.sleep(60)
    except Exception as e:
        print("LOOP ERROR", e); time.sleep(60)
