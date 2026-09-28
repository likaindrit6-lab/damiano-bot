import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
app=Flask(__name__)
@app.route('/')
def home():return "BOT FIX BLOCCO V1"
threading.Thread(target=lambda:app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()

def tg(m):
 print(m,flush=True)
 try:requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":m,"parse_mode":"HTML"},timeout=20)
 except:pass

def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10)
  if r.status_code==429:return "LIMIT"
  return r.json().get("response",[])
 except:return []

time.sleep(3)
tg("✅ BOT FIX BLOCCO ATTIVO - 5 MIN")

avvisati_gol={};avvisati_squadra=set();preavvisati=set();preavvisati_1t=set();stats_cache={};ultimo_hb=0

def get_stat(arr,nome):
 for s in arr:
  if s['type']==nome:
   try:return int(str(s['value']).replace('%','')or 0)
   except:return 0
 return 0

while True:
 try:
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   print(f"SLEEP NOTTE {now.strftime('%H:%M')}",flush=True)
   time.sleep(1800);continue

  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT":
   print("LIMIT - pausa 1h",flush=True)
   time.sleep(3600);continue

  print(f"CHECK {now.strftime('%H:%M')} - {len(live)} live",flush=True)

  if time.time()-ultimo_hb>14400:
   tg(f"✅ VIVO - {len(live)} live - {now.strftime('%H:%M')}")
   ultimo_hb=time.time()

  if len(live)==0:
   time.sleep(180);continue

  # --- FIX BLOCCO: prendo stats solo per 4 partite max ---
  cont_stats=0
  for g in live:
   m=g["fixture"]["status"]["elapsed"]or 0
   if m<55 or m>92:continue
   if cont_stats>=4:break
   fid=g["fixture"]["id"]
   d=stats_cache.get(fid)
   if not d or time.time()-d.get('time',0)>600:
    try:
     st=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if st and len(st)>=2:
      hs=st[0]['statistics'];aws=st[1]['statistics']
      sot=get_stat(hs,'Shots on Goal')+get_stat(aws,'Shots on Goal')
      tot=get_stat(hs,'Total Shots')+get_stat(aws,'Total Shots')
      dang=get_stat(hs,'Dangerous Attacks')+get_stat(aws,'Dangerous Attacks')
      perc=0
      if sot>=5 and dang>=35:perc=92
      elif sot>=4 and dang>=28:perc=89
      elif sot>=3 and dang>=25:perc=86
      elif sot>=2 and dang>=20:perc=82
      stats_cache[fid]={'perc':perc,'sot':sot,'time':time.time()}
      cont_stats+=1
      time.sleep(0.5)
    except:pass

  for g in live:
   m=g["fixture"]["status"]["elapsed"]or 0
   if m<20 or m>92:continue
   fid=g["fixture"]["id"];home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
   sot_tot=stats_cache.get(fid,{}).get('sot',0)
   perc=stats_cache.get(fid,{}).get('perc',0)

   if 20<=m<=45 and fid not in preavvisati_1t and perc>=85:
    tg(f"⚽️ 1T >{perc}% {m}' {home} {gh}-{ga} {away} TiriP:{sot_tot}");preavvisati_1t.add(fid)
   if 60<=m<=69 and fid not in preavvisati and perc>=80:
    tg(f"👀 PREPARATI {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away}");preavvisati.add(fid)
   if 70<=m<=92 and fid not in avvisati_squadra and sot_tot>=5:
    squadra=home if gh<=ga else away
    tg(f"🔥 GIOCALO {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away} NEXT {squadra}")
    avvisati_squadra.add(fid);avvisati_gol[fid]=gh+ga

  for g in live:
   fid=g["fixture"]["id"]
   if fid in avvisati_gol:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>avvisati_gol[fid]:tg(f"✅ GOL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del avvisati_gol[fid]

  time.sleep(300)
 except Exception as e:print(f"ERR {e}",flush=True);time.sleep(30)
