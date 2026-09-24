import os, time, requests
from datetime import datetime

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t, "parse_mode":"Markdown"}, timeout=15)
    except: pass

def get_stats(fid):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=15).json()
        sot=shots=dang=0
        for tm in r.get("response", []):
            for st in tm.get("statistics", []):
                if st["type"]=="Shots on Goal": sot+=st["value"] or 0
                if st["type"]=="Total Shots": shots+=st["value"] or 0
                if st["type"]=="Dangerous Attacks": dang+=st["value"] or 0
        return sot, shots, dang
    except: return 0,0,0

def calcola_prob(sot, shots, dang, minute):
    prob = sot*12 + shots*2 + dang*0.7
    if minute >= 60: prob+=10
    if minute >= 75: prob+=12
    return min(94, max(10, int(prob)))

send("✅ BOT DAMI V13.4 LIVE - % GOL 0'-90' ATTIVA")

inviate=set()
rosso=set()

while True:
    try:
        live=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json().get("response", [])
        for m in live:
            fid=m["fixture"]["id"]
            minute=m["fixture"]["status"]["elapsed"] or 0
            if minute==0 or minute>90: continue
            home=m["teams"]["home"]["name"]; away=m["teams"]["away"]["name"]
            country=m["league"]["country"]; league=m["league"]["name"]
            gh=m["goals"]["home"]; ga=m["goals"]["away"]

            # ROSSO sempre 0-90
            if fid not in rosso:
                try:
                    ev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json()
                    for e in ev.get("response", []):
                        if e["type"]=="Card" and e["detail"]=="Red Card":
                            send(f"🟥 *ROSSO {minute}'*\n*{country} {league}*\n{home} vs {away} ({gh}-{ga})")
                            rosso.add(fid)
                except: pass

            sot, shots, dang = get_stats(fid)
            prob = calcola_prob(sot, shots, dang, minute)

            # DA 0 A 90 - QUELLO CHE VOLEVI TU
            key = f"{fid}_{minute//15}" # manda ogni 15 min se prob alta
            if prob >= 70 and key not in inviate:
                if sot >=3: # solo se sta tirando
                    send(f"⚽️ *{minute}' {prob}% GOL*\n*{country} {league}*\n{home} vs {away} ({gh}-{ga})\nTiri: {sot} | Tot tiri: {shots} | Att: {dang}")
                    inviate.add(key)
            
            # CALDA / MORTA primo tempo come prima
            if minute <=45 and fid not in inviate:
                if sot>=4:
                    send(f"🔥 *CALDA {sot} TIRI {minute}' - {prob}% GOL*\n*{country} {league}*\n{home} vs {away}")
                    inviate.add(fid)
                elif sot<=2 and minute>=35 and sot>0:
                    send(f"💀 *MORTA {sot} TIRI {minute}' - {prob}% GOL*\n*{country} {league}*\n{home} vs {away}")
                    inviate.add(fid)

        time.sleep(60)
    except Exception as e:
        print(e); time.sleep(60)
