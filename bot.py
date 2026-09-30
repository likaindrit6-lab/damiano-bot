import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
app=Flask(__name__)
@app.route('/')
def home():return "BOT OK 30 - TUTTO A POSTO"
threading.Thread(target=lambda:app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()
def tg(m):
 print(m,flush=True)
 try:
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":m,"parse_mode":"HTML"},timeout=20)
 except:
  pass
def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=25)
  if r.status_code==429:return "LIMIT"
  return r.json().get("response",[])
 except:
  return []
def salva_file(nome,data):
 try:
  with open(f"/tmp/{nome}.json","w")as f:json.dump(data,f)
 except:
  pass
def leggi_file(nome):
 try:
  with open(f"/tmp/{nome}.json","r")as f:return json.load(f)
 except:
  return None
def check_vincita(fid,tipo):
 try:
  fx=api_get(f"https://v3.football.api-sports.io/fixtures?id={fid}")
  if not fx:return None
  f=fx[0]
  if f['fixture']['status']['short']not in['FT','AET','PEN']:return None
  gh=f['goals']['home'];ga=f['goals']['away']
  if gh is None:return None
  t=tipo.lower()
  if"home"in t or"1 fisso"in t:return gh>ga
  if"x2"in t:return ga>=gh
  if"over 0.5"in t:return(gh+ga)>=1
  if"over 1.5"in t:return(gh+ga)>=2
  if"casa segna"in t:return gh>=1
  return None
 except:
  return None
time.sleep(3)
tg("✅ BOT FINALE - TUTTO A POSTO - 2 SCHEDINE 30MIN")
avvisati_gol={};avvisati_squadra=set();preavvisati=set();preavvisati_1t=set();stats_cache={};bombe_fatte=False;ultimo_hb=0;ultima_schedina=0;ultima_pre_schedina=0
def get_stat(arr,nome):
 for s in arr:
  if s['type']==nome:
   try:
    return int(str(s['value']).replace('%','')or 0)
   except:
    return 0
 return 0
def get_sot(fid):
 d=stats_cache.get(fid)
 if d:return d.get('sot',0)
 return 0
while True:
 try:
  now=datetime.now(ITALY)
  if 0<=now.hour<7:
   if now.hour==0:bombe_fatte=False;avvisati_squadra.clear();preavvisati.clear();preavvisati_1t.clear();avvisati_gol.clear();stats_cache.clear()
   time.sleep(1800);continue
  if time.time()-ultimo_hb>900:
   lc=api_get("https://v3.football.api-sports.io/fixtures?live=all")
   if lc=="LIMIT":time.sleep(3600);continue
   tg(f"✅ VIVO - {len(lc)} live - {now.strftime('%H:%M')}")
   ultimo_hb=time.time()
  if not bombe_fatte and now.hour>=7 and now.hour<9:
   fix=api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
   fix=[x for x in fix if x['fixture']['status']['short']=='NS']
   bombe=[];madre_save=[];cand_prog=[]
   for g in fix[:90]:
    if len(bombe)>=30:break
    odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={g['fixture']['id']}")
    if odds=="LIMIT":time.sleep(3600);continue
    if not odds:time.sleep(0.2);continue
    for o in odds:
     for bk in o.get("bookmakers",[])[:2]:
      for bet in bk.get("bets",[]):
       for v in bet["values"]:
        try:
         q=float(v["odd"])
         ora=datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY).strftime('%H:%M')
         base={"id":g['fixture']['id'],"match":f"{g['teams']['home']['name']} vs {g['teams']['away']['name']}","ora":ora,"quota":q,"tipo":f"{bet['name']} {v['value']}"}
         if bet["name"]=="Match Winner" and 1.02<=q<=1.08:
          if len(bombe)<30:bombe.append(f"{ora} {g['teams']['home']['name']} vs {g['teams']['away']['name']} Q{q}\n");madre_save.append(base)
         if 1.08<=q<=1.30:
          bn=bet["name"].lower();val=v["value"].lower();safe=False
