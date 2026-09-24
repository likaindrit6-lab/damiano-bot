import os, time, requests
TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT=os.getenv("CHAT_ID")
API=os.getenv("API_FOOTBALL_KEY")
print(f"TOKEN ok? {bool(TOKEN)} CHAT ok? {bool(CHAT)} API ok? {bool(API)}", flush=True)
def send(m):
 try:
  r=requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",data={"chat_id":CHAT,"text":m},timeout=15)
  print(f"SEND {m} -> {r.status_code} {r.text[:100]}", flush=True)
 except Exception as e:
  print(f"ERRORE SEND: {e}", flush=True)
send("✅ V11 PARTITO - DIAGNOSI")
h={"x-apisports-key":API}
while True:
 time.sleep(60)
 send("✅ SONO VIVO")
