import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
av_g={};av_s=set();pre=set();pre1=set();cache={}
try:
 base=f"https://api.telegram.org/bot{BOT_TOKEN}"
 requests.get(base+"/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass
app=Flask(__name__)
@app.route('/')
def home(): return f"BOT OK - {'PAUSA' if is_paused else 'ATTIVO'}",200
def run_flask():
 from waitress import serve
 serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()
TASTIERA=json.dumps({"keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"]],"resize_keyboard":True})
def tg(m,cid=None):
 try:
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":cid or CHAT_ID,"text":m,"parse_mode":"HTML","reply_markup":TASTIERA},timeout=20)
 except: pass
def api_get(u):
 try:
  r=requests.get(u,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=20)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []
def poll():
 global is_paused,last_update_id
 while True:
  try:
   r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=20",timeout=25).json()
   for up in r.get("result",[]):
    last_update_id=up["update_id"]
    t=up.get("message",{}).get("text","").lower()
    c=up.get("message",{}).get("chat",{}).get("id")
    if "spegni" in t: is_paused=True; tg("🛑 PAUSA",c)
    if "accendi" in t or "/start" in t: is_paused=False; tg("✅ ATTIVO - Bot ripartito",c)
    if "status" in t: tg(f"✅ SONO VIVO - {datetime.now(ITALY).strftime('%H:%M')}",c)
    if "bolla" in t: tg("Bolla test - se leggi questo il bot va",c)
  except: pass
  time.sleep(3)
threading.Thread(target=poll,daemon=True).start()
tg("✅ BOT APPENA RIAVVIATO - Test",con_tastiera=False)
while True: time.sleep(60)
