import os, threading, time, requests
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "V21 FINAL OK"
port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}
BASE = "https://v3.football.api-sports.io"

def send(t):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=25)
        print(f"SEND {r.status_code}: {t[:60]}")
    except Exception as e:
        print("send error", e)

def is_orario_attivo():
    h = datetime.now().astimezone().hour
    return h >= 8 or h < 2

def get_stats(fid):
    try:
        r = requests.get(f"{BASE}/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=15).json()
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

def analizza_squadra(team_id):
    try:
        res = requests.get(f"{BASE}/fixtures?team={team_id}&last=5", headers=HEAD, timeout=15).json().get("response",[])
        gol_fatti=0; partite_con_gol=0; media_gol=0
        for m in res:
            gh=m["goals"]["home"]; ga=m["goals"]["away"]
            if gh is None or ga is None: continue
            is_home = m["teams"]["home"]["id"]==team_id
            fatti = gh if is_home else ga
            subiti = ga if is_home else gh
            media_gol += fatti + subiti
            if fatti>0: partite_con_gol+=1
            gol_fatti+=fatti
        if not res: return 0,0,0
        freq_gol = partite_con_gol / len(res) if res else 0
        avg = media_gol / len(res) if res else 0
        return freq_gol, avg, gol_fatti
    except: return 0,0,0

def get_liste_avanzate():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        fixtures = requests.get(f"{BASE}/fixtures?date={today}", headers=HEAD, timeout=25).json().get("response",[])
    except: fixtures=[]
    lista_over=[]; lista_corner=[]; lista_golgol=[]; picks_schedina=[]
    for f in fixtures[:80]:
        try:
            fid=f["fixture"]["id"]
            home=f["teams"]["home"]["name"]; away=f["teams"]["away"]["name"]
            hid=f["teams"]["home"]["id"]; aid=f["teams"]["away"]["id"]
            country=f["league"]["country"]; league=f["league"]["name"]
            ora=f["fixture"]["date"][11:16]
            nome_base=f"{ora} {home} vs {away} - {country} {league}"
            try:
                odds_f = requests.get(f"{BASE}/odds?fixture={fid}", headers=HEAD, timeout=15).json().get("response",[])
                if odds_f:
                    for book in odds_f[0].get("bookmakers",[])[:2]:
                        for bet in book.get("bets",[]):
                            bname=bet.get("name","").lower()
                            for v in bet.get("values",[]):
                                try:
                                    odd=float(v["odd"]); val=v["value"]
                                    if "corner" in bname and "Over 6.5" in val and odd <= 1.60:
                                        lista_corner.append(f"• {nome_base} @ {odd}")
                                    if "Over 1.5" in val and 1.28 <= odd <= 1.55:
                                        picks_schedina.append({"txt": f"{home} vs {away} - {country} {league} Over 1.5 @ {odd}", "q": odd})
                                except: continue
            except: pass
            time.sleep(0.3)
            freq_h, avg_h, _ = analizza_squadra(hid)
            freq_a, avg_a, _ = analizza_squadra(aid)
            if freq_h >= 0.8 and freq_a >= 0.8:
                lista_over.append(f"• {nome_base} - NO 0-0 99% (Casa {int(freq_h*100)}% - Ospite {int(freq_a*100)}%)")
                if avg_h >= 2.2 and avg_a >= 2.2: lista_over[-1] += " - OVER 1.5 ALTO"
            if freq_h >= 0.6 and freq_a >= 0.6 and avg_h >= 2.0 and avg_a >= 2.0:
                lista_golgol.append(f"• {nome_base} - GOL/GOL {int((freq_h+freq_a)/2*100)}%")
        except: continue
        time.sleep(0.2)
    lista_over = sorted(list(dict.fromkeys(lista_over)))
    lista_corner = sorted(list(dict.fromkeys(lista_corner)))
    lista_golgol = sorted(list(dict.fromkeys(lista_golgol)))
    picks_schedina = sorted(list({p['txt']: p for p in picks_schedina}.values()), key=lambda x: x['q'], reverse=True)
    quota=1; usate=[]
    for p in picks_schedina[:10]:
        quota*=p["q"]; usate.append(p)
        if quota >= 1.70: break
    if usate and quota >= 1.70:
        schedina = f"🎯 SCHEDINA 1.80 - Quota {quota:.2f}\n\n" + "\n".join([f"• {u['txt']}" for u in usate])
    else:
        schedina = "🎯 SCHEDINA 1.80: Oggi poche quote 1.30-1.55, uso lista NO 0-0 per live"
    return lista_over, lista_corner, schedina, lista_golgol

time.sleep(3)
send("BOT DAMI V21 ON - NO 0-0 + GOLGOL ✅")

inviate=set(); fatto_10=False; ultimo_golgol=0
while True:
    try:
        if not is_orario_attivo():
            time.sleep(300); continue
        now = datetime.now().astimezone()
        if not fatto_10 or (now.hour == 10 and now.minute < 5):
            over, corner, schedina, golgol = get_liste_avanzate()
            send(f"📋 OVER 1.5 / NO 0-0 99% OGGI ({len(over)})\n\n" + ("\n".join(over[:80]) if over else "Nessuna NO 0-0 oggi - controllo live"))
            time.sleep(1)
            send(f"🚩 CORNER 6.5 OGGI ({len(corner)})\n\n" + ("\n".join(corner[:80]) if corner else "Nessuna"))
            time.sleep(1)
            send(schedina)
            time.sleep(1)
            if golgol:
                send(f"⚽ GOL/GOL OGGI ({len(golgol)})\n\n" + "\n".join(golgol[:80]))
            fatto_10=True
            ultimo_golgol = time.time()
        if time.time() - ultimo_golgol > 7200:
            _, _, _, golgol = get_liste_avanzate()
            if golgol: send(f"⚽ GOL/GOL UPDATE ({len(golgol)})\n\n" + "\n".join(golgol[:80]))
            ultimo_golgol = time.time()
        live=requests.get(f"{BASE}/fixtures?live=all", headers=HEAD, timeout=20).json().get("response", [])
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
