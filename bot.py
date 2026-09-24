import os, time, requests
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or ""
TOKEN=TOKEN.strip()
CHAT = os.getenv("CHAT_ID","").strip()
API = os.getenv("API_FOOTBALL_KEY","").strip()

def send(t):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  data={"chat_id": CHAT, "text": t, "parse_mode":"Markdown"})

send("✅ BOT DAMI V7 FINALE - LOGICA 0-0 ATTIVA")

inviate=set()
while True:
    try:
        h={"x-apisports-key": API}
        r=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=h, timeout=20).json()
        for m in r.get("response",[]):
            if m["goals"]["home"]==0 and m["goals"]["away"]==0:
                minute=m["fixture"]["status"]["elapsed"]
                if minute and 10 <= minute <= 75:
                    idd=m["fixture"]["id"]
                    if idd not in inviate:
                        txt=f"⚽️ *0-0 al {minute}'* \n{m['teams']['home']['name']} - {m['teams']['away']['name']}\nID:{idd}"
                        send(txt)
                        inviate.add(idd)
        time.sleep(60)
    except Exception as e:
        print(e)
        time.sleep(60)
