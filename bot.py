import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
app=Flask(__name__)
@app.route('/')
def home():return "BOT 10-24 FIX 4H"
threading.Thread(target=lambda:app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()

def tg(m):
 print(m,flush=True)
 try:requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":m,"parse_mode":"HTML"},timeout=20)
 except:pass

def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=25)
  if r.status_code==429:return "LIMIT"
  return r.json().get("response",[])
 except:return []

def salva_file(nome,data):
 try:
  with open(f"/tmp/{nome}.json","w")as f:json.dump(data,f)
 except:pass

def leggi_file(nome):
 try:
  with open(f"/tmp/{nome}.json","r")as f:return json.load(f)
 except:return None

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
 except:return None

time.sleep(3)
tg("✅ BOT 10:00-24:00 ATTIVO - FIX 4 ORE")

avvisati_gol={};avvisati_squadra=set();preavvisati=set();preavvisati_1t=set();stats_cache={};bombe_fatte=False;ultimo_hb=0;ultima_schedina=0;ultima_pre_schedina=0

def get_stat(arr,nome):
 for s in arr:
  if s['type']==nome:
   try:return int(str(s['value']).replace('%','')or 0)
   except:return 0
 return 0

def get_sot(fid):
 d=stats_cache.get(fid)
 if d:return d.get('sot',0)
 return 0

while True:
 try:
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:bombe_fatte=False;avvisati_squadra.clear();preavvisati.clear();preavvisati_1t.clear();avvisati_gol.clear();stats_cache.clear()
   print(f"SLEEP NOTTE {now.strftime('%H:%M')}",flush=True)
   time.sleep(1800);continue

  # --- FIX: VIVO ogni 4 ore ma partite ogni 5 min ---
  deve_mandare_vivo = False
  if time.time()-ultimo_hb>14400:
   deve_mandare_vivo = True

  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT":
   print("LIMIT API - pausa 1h",flush=True)
   time.sleep(3600);continue

  print(f"CHECK {now.strftime('%H:%M')} - {len(live)} live",flush=True)

  if deve_mandare_vivo:
   tg(f"✅ VIVO - {len(live)} live - {now.strftime('%H:%M')}")
   ultimo_hb=time.time()

  if len(live)==0:time.sleep(180);continue

  TTL_STATS=600;SLEEP_LOOP=300
  cand_schedina=[];cand_pre_55=[]
  for g in live:
   m=g["fixture"]["status"]["elapsed"]or 0
   if m<20 or m>92:continue
   fid=g["fixture"]["id"];home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away']
   d=stats_cache.get(fid)
   if not d or time.time()-d.get('time',0)>TTL_STATS:
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
      elif sot>=3 and dang>=25 and tot>=7:perc=86
      elif sot>=2 and dang>=20:perc=82
      stats_cache[fid]={'perc':perc,'sot':sot,'time':time.time()}
      time.sleep(0.4)
    except:pass
   sot_tot=get_sot(fid)
   if 20<=m<=45 and fid not in preavvisati_1t:
    d=stats_cache.get(fid,{})
    if d.get('perc',0)>=85 and d.get('sot',0)>=3:tg(f"⚽️ 1T >{d['perc']}% {m}' {home} {gh}-{ga} {away} TiriP:{d['sot']}");preavvisati_1t.add(fid)
   if m>=60 and sot_tot<5:continue
   if 70<=m<=85:cand_schedina.append(g)
   if 55<=m<=69:
    dd=stats_cache.get(fid,{})
    if dd.get('perc',0)>=80:cand_pre_55.append(g)
   if m<60:continue
   perc=min(96,70+(m-45))
   if 60<=m<=69 and fid not in preavvisati:tg(f"👀 PREPARATI {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away}");preavvisati.add(fid)
   if 70<=m<=92 and fid not in avvisati_squadra:
    squadra=home if gh<=ga else away
    tg(f"🔥 GIOCALO {m}' >{perc}% TiriP:{sot_tot} {home} {gh}-{ga} {away} NEXT {squadra}")
    avvisati_squadra.add(fid);avvisati_gol[fid]=gh+ga

  for g in live:
   fid=g["fixture"]["id"]
   if fid in avvisati_gol:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>avvisati_gol[fid]:tg(f"✅ GOL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del avvisati_gol[fid]

  if time.time()-ultima_pre_schedina>1800 and len(cand_pre_55)>=3:
   txt=f"👀 PRE-SCHEDINA 55' >80% - TRA 10 MIN! {now.strftime('%H:%M')}\n\n"
   for g in cand_pre_55[:4]:
    dd=stats_cache.get(g['fixture']['id'],{})
    txt+=f"{g['fixture']['status']['elapsed']}' {dd.get('perc',0)}% TiriP:{get_sot(g['fixture']['id'])} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n\n"
   tg(txt);ultima_pre_schedina=time.time()

  if time.time()-ultima_schedina>1800 and len(cand_schedina)>=3:
   txt=f"🔥 SCHEDINA 70' >90% - 4 PARTITE {now.strftime('%H:%M')}\n\n"
   for g in cand_schedina[:4]:txt+=f"{g['fixture']['status']['elapsed']}' TiriP:{get_sot(g['fixture']['id'])} {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\n\n"
   tg(txt);ultima_schedina=time.time()

  time.sleep(SLEEP_LOOP)
 except Exception as e:print(f"ERR {e}",flush=True);time.sleep(30)
