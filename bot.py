import os, time, requests
from flask import Flask
import threading

# FIX RENDER OBBLIGATORIO SENNO' DA STATUS 1
app = Flask(__name__)
@app.route('/')
def home(): return "OK"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
CHAT = (os.getenv("CHAT_ID") or "606420824").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()
HEAD = {"x-apisports-key": API}

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": t}, timeout=15)
    except: pass

def get_stats(fid):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=15).json()
        sot=shots=dang=corners=att=0
        for tm in r.get("response", []):
            for st in tm.get("statistics", []):
                if st["type"]=="Shots on Goal": sot+=st["value"] or 0
                if st["type"]=="Total Shots": shots+=st["value"] or 0
                if st["type"]=="Attacks": att+=st["value"] or 0
                if st["type"]=="Dangerous Attacks": dang+=st["value"] or 0
                if st["type"]=="Corner Kicks": corners+=st["value"] or 0
        final_att = dang if dang>0 else att
        return sot, shots, final_att, corners
    except: return 0,0,0,0

def get_corner_minuti(fid):
    try:
        ev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json()
        minuti=[]
        for e in ev.get("response", []):
            if e.get("detail")=="Corner Kick" or e["type"]=="Corner":
                minuti.append(f"{e['time']['elapsed']}'")
        return minuti
    except: return []

def calcola_prob(sot, shots, dang, minute):
    prob = sot*12 + shots*2 + dang*0.7
    if minute >= 60: prob+=10
    if minute >= 75: prob+=12
    return min(94, max(10, int(prob)))

send("BOT DAMI V13.4 ORIGINALE RIPARTITO")

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

            if fid not in rosso:
                try:
                    ev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json()
                    for e in ev.get("response", []):
                        if e["type"]=="Card" and e["detail"]=="Red Card":
                            send(f"ROSSO {minute}' {country} {league} {home} vs {away} ({gh}-{ga})")
                            rosso.add(fid)
                except: pass

            sot, shots, dang, corners = get_stats(fid)
            prob = calcola_prob(sot, shots, dang, minute)

            key = f"{fid}_{minute//15}"
            if prob >= 70 and key not in inviate:
                if sot >=3:
                    c_min = get_corner_minuti(fid)
                    c_txt = f"Corner: {corners}"
                    if c_min:
                        c_txt += f" ({', '.join(c_min[-5:])})"
                    send(f"{minute}' {prob}% GOL {country} {league} {home} vs {away} ({gh}-{ga}) Tiri: {sot} | Tot tiri: {shots} | Att: {dang} | {c_txt}")
                    inviate.add(key)
            
            if minute <=45 and fid not in inviate:
                if sot>=4:
                    send(f"CALDA {sot} TIRI {minute}' - {prob}% GOL {country} {league} {home} vs {away}")
                    inviate.add(fid)
                elif sot<=2 and minute>=35 and sot>0:
                    send(f"MORTA {sot} TIRI {minute}' - {prob}% GOL {country} {league} {home} vs {away}")
                    inviate.add(fid)

        time.sleep(60)
    except Exception as e:
        print(e); time.sleep(60)
