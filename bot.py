import os, time, requests
TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT=os.getenv("CHAT_ID")
API=os.getenv("API_FOOTBALL_KEY")
def send(m):
 try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",data={"chat_id":CHAT,"text":m},timeout=15)
 except: pass
send("✅ V11 PARTITO - FIX pytz")
h={"x-apisports-key":API}
while True:
 try:
  live=requests.get("https://v3.football.api-sports.io/fixtures?live=all",headers=h,timeout=20).json().get("response",[])
  for x in live:
   try:
    f=x["fixture"];g=x["goals"];mi=f["status"]["elapsed"] or 0
    if g["home"]!=0 or g["away"]!=0: continue
    if mi<20 or mi>85: continue
    fid=f["id"];home=x["teams"]["home"]["name"];away=x["teams"]["away"]["name"]
    s=requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}",headers=h,timeout=15).json().get("response",[])
    if len(s)<2: continue
    def get(a,n):
     for z in a:
      if n.lower() in z["type"].lower(): return z["value"] or 0
     return 0
    tiri=get(s[0]["statistics"],"Shots on Goal")+get(s[1]["statistics"],"Shots on Goal")
    corn=get(s[0]["statistics"],"Corner")+get(s[1]["statistics"],"Corner")
    if 30<=mi<=55:
     if tiri>=4 and corn>=4: send(f"CALDA {mi}' {home}-{away} 0-0 T:{tiri} C:{corn}")
     elif tiri<=1 and corn<=2: send(f"FREDDA {mi}' {home}-{away} 0-0 T:{tiri} C:{corn}")
   except: continue
  time.sleep(60)
 except: time.sleep(30)
