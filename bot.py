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

def get_sot(fid):
    try:
        r=requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEAD, timeout=15).json()
        s=0
        for tm in r.get("response",[]):
            for st in tm.get("statistics",[]):
                if st["type"]=="Shots on Goal": s+= st["value"] or 0
        return s
    except: return 0

def get_avg(team_id):
    try:
        r=requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEAD, timeout=15).json()
        tot=0; c=0
        for f in r.get("response",[]):
            tot+= f["goals"]["home"]+f["goals"]["away"]; c+=1
        return tot/c if c else 0
    except: return 0

send("✅ BOT DAMI V12 - BASE 21:33 OK\nCalda 4 tiri | Morta 2 tiri | Rosso | 1 Schedina 10:00 quota 1.80 | 3 Goal ogni 2h")

inviate=set(); rosso=set(); schedina_oggi=""; ultimo_gg=0

while True:
    try:
        now=datetime.now()
        today=now.strftime("%Y-%m-%d")
        live=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEAD, timeout=20).json().get("response",[])

        for m in live:
            fid=m["fixture"]["id"]
            minute=m["fixture"]["status"]["elapsed"] or 0
            
            # ROSSO
            if fid not in rosso:
                ev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=HEAD, timeout=10).json().get("response",[])
                for e in ev:
                    if e["type"]=="Card" and e["detail"]=="Red Card":
                        send(f"🟥 *ROSSO {minute}'*\n*{m['league']['country']} {m['league']['name']}*\n{m['teams']['home']['name']} vs {m['teams']['away']['name']}")
                        rosso.add(fid)
            
            # TIRI 4 = CALDA, 2 = MORTA entro 45' - qualsiasi risultato
            if fid in inviate or minute==0 or minute>45: continue
