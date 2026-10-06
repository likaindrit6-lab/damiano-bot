import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv('BOT_TOKEN')
CHAT_ID=os.getenv('CHAT_ID')
API_FOOTBALL_KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_update_id=0;av_g={};av_s=set();pre=set();pre1=set();cache={};tripla_coda=[];ultimo_invio_tripla=time.time()
try:
 requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true',timeout=10)
except: pass
app=Flask(__name__)
@app.route('/')
def home():
 stato='PAUSA' if is_paused else 'ATTIVO'
 return f'BOT V14.3.1 ITALIA FIX - {stato}',200
def run_flask():
 from waitress import serve
 serve(app,host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
threading.Thread(target=run_flask,daemon=True).start()
TASTIERA_JSON=json.dumps({'keyboard':[['ACCONDI','SPEGNI'],['BOLLA','STATUS']],'resize_keyboard':True,'is_persistent':True})
def tg(m,chat_id=None,con_tastiera=False):
 try:
  cid=chat_id if chat_id else CHAT_ID
  payload={'chat_id':cid,'text':m,'parse_mode':'HTML','disable_web_page_preview':True}
  if con_tastiera: payload['reply_markup']=TASTIERA_JSON
  requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',json=payload,timeout=25)
 except: pass
def api_get(url):
 try:
  r=requests.get(url,headers={'x-apisports-key':API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429: return 'LIMIT'
  return r.json().get('response',[])
 except: return []
def get_stat(arr,name):
 for s in arr:
  if s.get('type')==name:
   try:
    v=str(s.get('value') or 0).replace('%','').strip()
    return int(v or 0)
   except: return 0
 return 0
def get_flag(p): return p[:2].upper()
def get_tiri(fid):
 try:
  d=cache.get(fid);now_t=time.time()
  if not d or now_t-d.get('time',0)>180:
   u='https://v3.football.api-sports.io/fixtures/statistics?fixture='+str(fid)
   s=api_get(u)
   if s and len(s)>=2:
    sa=s[0].get('statistics',[]);sb=s[1].get('statistics',[])
    v1=get_stat(sa,'Shots on Goal');v2=get_stat(sb,'Shots on Goal')
    sot=v1+v2;cache[fid]={'sot':sot,'time':now_t};time.sleep(0.4);return sot
   if d: return d.get('sot',0)
   return 0
  return d.get('sot',0)
 except: return 0
def crea_bolla_15():
 try:
  OGGI=datetime.now(ITALY).strftime('%Y-%m-%d')
  u='https://v3.football.api-sports.io/fixtures?date='+OGGI
  fixtures=api_get(u)
  if not fixtures: return f'Nessuna partita oggi {OGGI}'
  picks=[];quota_tot=1.0
  fixtures=sorted(fixtures,key=lambda x: x['fixture']['timestamp'])
  for p in fixtures:
   if len(picks)>=12: break
   if quota_tot>=3.35: break
   fid=p['fixture']['id'];dt=datetime.fromtimestamp(p['fixture']['timestamp'],tz=ITALY)
   if dt < datetime.now(ITALY): continue
   home=p['teams']['home']['name'];away=p['teams']['away']['name'];paese=p['league']['country'];orario=dt.strftime('%H:%M')
   qenc=urllib.parse.quote(home+' '+away)
   link_web='https://www.bet365.it/#/AX/K^'+qenc
   link_google='https://www.google.com/search?q=site:bet365.it+'+qenc
   link_stats='https://www.flashscore.it/search/?q='+qenc
   u2='https://v3.football.api-sports.io/odds?fixture='+str(fid)
   odds=api_get(u2)
   if not odds or odds=='LIMIT': continue
   if not odds[0].get('bookmakers'): continue
   book=None
   for b in odds[0]['bookmakers']:
    if b['id']==8 or '365' in b['name']:
     book=b;break
   if not book: book=odds[0]['bookmakers'][0]
   best=None
   for bet in book['bets']:
    if bet['name'] not in ['Match Winner','Double Chance','Both Teams To Score','Goals Over/Under']: continue
    for v in bet['values']:
     try:
      q=float(v['odd'])
      if 1.08 <= q <= 1.30:
       if best is None or q>best['q']:
        best={'m':bet['name'],'e':v['value'],'q':q}
     except: continue
   if not best: continue
   if quota_tot*best['q']>3.45: continue
   m_name=best['m'];m_val=best['e']
   if 'Match Winner' in m_name: txt='VINCENTE: 1' if 'Home' in m_val else 'VINCENTE: 2' if 'Away' in m_val else 'VINCENTE: X'
   elif 'Double Chance' in m_name:
    v=m_val.replace('Home/Draw','1X').replace('Draw/Away','X2').replace('Home/Away','12');txt='DOP
