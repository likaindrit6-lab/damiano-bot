import os, time, requests
TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT=os.getenv("CHAT_ID")
API=os.getenv("API_FOOTBALL_KEY")

def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",data={"chat_id":CHAT,"text":m},timeout=10)
    except: pass

send("✅ TEST CONNESSIONE - ARRIVA TUTTO")

h={"x-apisports-key":API}

while True:
    try:
        r=requests.get("https://v3.football.api-sports.io/fixtures?live=all",headers=h,timeout=20).json().get("response",[])
        if not r:
            send("Sono vivo ma ora non c'è nessuna partita live")
        else:
            for x in r[:3]: # ti mando le prime 3 live, qualsiasi risultato
                mi=x["fixture"]["status"]["elapsed"] or 0
                home=x["teams"]["home"]["name"]
                away=x["teams"]["away"]["name"]
                gh=x["goals"]["home"]
                ga=x["goals"]["away"]
                send(f"⚽️ {mi}' {home} {gh}-{ga} {away} - TEST CHE ARRIVA")
        time.sleep(60)
    except Exception as e:
        send(f"Errore: {e}")
        time.sleep(30)
