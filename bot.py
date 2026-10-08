import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv('BOT_TOKEN')
CHAT_ID=os.getenv('CHAT_ID')
API_FOOTBALL_KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False
last_update_id=0
ultimo_gol={}
ultima_schedina_ora=-1
schedina_attiva=[]
schedina_notificata=set()
live_inviate=set()
if BOT_TOKEN:
 try:
  requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true',timeout=10)
 except:
  pass
app=Flask(__name__)
@app.route('/')
def home():
 return 'V40 OK',200
@app.route('/health')
def health():
 return 'OK',200
TASTIERA=json.dumps({'keyboard':[['ACCENDI','SPEGNI'],['BLASONATE LUN-DOM','PARTITE OGGI'],['SCHEDINA ORA','TOKEN']],'resize_keyboard':True})
def tg(m,chat_id=None,con_tastiera=False):
 try:
  cid=chat_id or CHAT_ID
  url=f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
  p={'chat_id':cid,'text':m,'parse_mode':'HTML'}
  if con_tastiera:
   p['reply_markup']=TASTIERA
  requests.post(url,json=p,timeout=15)
 except:
  pass
def api_get(url):
 if is_paused:
  return
