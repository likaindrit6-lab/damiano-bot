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

# --- ORARIO 08:00 -> 02:00 ---
def is_orario_attivo():
    h = datetime.now().hour
    if h >= 8: return True
    if h < 2: return True
    return False

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
    return min(
