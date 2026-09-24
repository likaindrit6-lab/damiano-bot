import os, time, requests
TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT=os.getenv("CHAT_ID")
API=os.getenv("API_FOOTBALL_KEY")
def send(m):
 try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",data={"chat_id":CHAT,"text":m},timeout=10)
 except: pass
send("✅ BOT PARTITO - FINITO")
h={"x-apisports-key":API}
while True:
 time.sleep(60)
