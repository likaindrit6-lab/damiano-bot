import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

is_paused=False
last_update_id=0
av_g={};av_s=set();pre=set();pre1=set();cache={}
tripla_coda=[];ultimo_invio_tripla=time.time()

try:
 requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
except: pass

app=Flask(__name__)
@app.route('/')
def home():
    return f"BOT V16 FIX LINK - {'PAUSA' if is_paused else 'ATTIVO'}",200

def run_flask():
 from waitress import serve
 serve(app,host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

TASTIERA_JSON=json.dumps({"keyboard":[["🟢 ACCENDI","🔴 SPEGNI"],["🎫 BOLLA","📊 STATUS"]],"resize_keyboard":True,"is_persistent":True})

def tg(m,chat_id=None,con_tastiera=False):
 try:
  cid=chat_id if chat_id else CHAT_ID
  payload={"chat_id":cid,"text":m,"parse_mode":"HTML","disable_web_page_preview":True}
  if con_tastiera: payload["reply_markup"]=TASTIERA_JSON
  requests.post(f"https://api.telegram.org/bot
