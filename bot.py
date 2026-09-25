import os, time, requests
from datetime import datetime
from flask import Flask
import threading

# MINI SERVER PER RENDER - OBBLIGATORIO
app = Flask(__name__)
@app.route('/')
def home(): return "BOT DAMI LIVE OK"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web, daemon=True).start()

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

def get_media_gol(team_id):
    try:
        r = requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEAD, timeout=10).json()
        resp = r.get("response", [])
        if len(resp) < 3: return 0
        tot = sum((p["goals"]["home"] or 0) + (p["goals"]["away"] or 0) for p in resp)
        return tot / len(resp)
    except: return 0

send("✅ BOT DAMI V13.4 LIVE - FIX RENDER OK")

inviate=set()
rosso=set()
schedina_oggi=""

while True:
    try:
        ora = datetime.now()
        # SCHEDINA 10:00 QUOTA 1.8
        if ora.hour == 10 and ora.minute < 4 and schedina_oggi != ora.strftime("%Y-%m-%d"):
            try:
                today = ora.strftime("%Y-%m-%d")
                fixtures = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers=HEAD, timeout=15).json().get("response", [])
                filtrate=[]
                for f in fixtures:
                    if f["fixture"]["status"]["short"] != "NS": continue
                    mh=get_media_gol(f["teams"]["home"]["id"])
                    ma=get_media_gol(f["teams"]["away"]["id"])
                    time.sleep(0.3)
                    if (mh+ma)/2 >= 2.0:
                        filtrate.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} ({round((mh+ma)/2,1)} gol)")
                    if len(filtrate)>=6: break
                if len(filtrate)>=3:
                    txt=f"🎫 *SCHEDINA 10:00 QUOTA 1.8*\n*{ora.strftime('%d/%m')}*\n\n" + "\n".join([f"{i+1}. {p}" for i,p in enumerate(filtrate)])
                    send(txt)
                    schedina_oggi=today
            except: pass

        # LIVE
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
                            send(f"🟥 *ROSSO {minute}'*\n*{country} {league}*\n{home} vs {away} ({gh}-{ga})")
                            rosso.add(fid)
                except: pass

            sot, shots, dang, corners = get_stats(fid)
            prob = calcola_prob(sot, shots, dang, minute)

            key = f"{fid}_{minute//15}"
            if prob >= 70 and key not in inviate:
                if sot >=3:
                    c_min = get_corner_minuti(fid)
                    c_txt = f"Corner: {corners}"
                    if c_min: c_txt += f" ({', '.join(c_min[-5:])})"
                    send(f"⚽️ *{minute}' {prob}% GOL*\n*{country} {league}*\n{home} vs {away} ({gh}-{ga})\nTiri: {sot} | Tot tiri: {shots} | Att: {dang} | {c_txt}")
                    inviate.add(key)
            
            if minute <=45 and fid not in inviate:
                if sot>=4:
                    send(f"🔥 *CALDA {sot} TIRI {minute}' - {prob}% GOL*\n*{country} {league}*\n{home} vs {away}")
                    inviate.add(fid)
                elif sot<=2 and minute>=35 and sot>0:
                    send(f"💀 *MORTA {sot} TIRI {minute}' - {prob}% GOL*\n*{country} {league}*\n{home} vs {away}")
                    inviate.add(fid)
            time.sleep(0.5)

        time.sleep(60)
    except Exception as e:
        print(e); time.sleep(60)
