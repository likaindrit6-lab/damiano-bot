import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
app=Flask(__name__)
@app.route('/')
def home():return "BOT V16 >85% SU TUTTO OK"
threading.Thread(target=lambda:app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()

def tg(m):
 print(m,flush=True)
 try:requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":m,"parse_mode":"HTML"},timeout=15)
 except:pass

def api_get(url,t=8):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_KEY},timeout=t)
  if r.status_code==429:return "LIMIT"
  return r.json().get("response",[])
 except:return []

def salva(n,d):
 try:json.dump(d,open(f"/tmp/{n}.json","w"))
 except:pass
def leggi(n):
 try:return json.load(open(f"/tmp/{n}.json","r"))
 except:return None

def get_stat(arr,nome):
 for s in arr:
  if s['type']==nome:
   try:return int(str(s['value']).replace('%','')or 0)
   except:return 0
 return 0

avv_pre_pt=set(leggi("avv_pre_pt") or [])
avv_pt=set(leggi("avv_pt") or [])
avv_pre=set(leggi("avv_pre") or [])
avv_giocalo=set(leggi("avv_giocalo") or [])
stats_cache={};ultimo_vivo=0
ultima_pre_tripla=0;ultima_tripla=0

def vivo_thread():
 global ultimo_vivo
 while True:
  try:
   now=datetime.now(ITALY)
   if 0<=now.hour<10:time.sleep(900);continue
   if time.time()-ultimo_vivo>900:
    lc=api_get("https://v3.football.api-sports.io/fixtures?live=all",t=8)
    if lc!="LIMIT" and lc:
     tg(f"✅ VIVO V16 - {len(lc)} live - {now.strftime('%H:%M')} >85%")
     ultimo_vivo=time.time()
   time.sleep(60)
  except:time.sleep(60)
threading.Thread(target=vivo_thread,daemon=True).start()

time.sleep(3)
tg("✅ BOT V16 PARTITO - TUTTO >85% - 6 TIRI >85%")

while True:
 try:
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:
    avv_pre_pt.clear();avv_pt.clear();avv_pre.clear();avv_giocalo.clear();stats_cache.clear()
    salva("avv_pre_pt",[]);salva("avv_pt",[]);salva("avv_pre",[]);salva("avv_giocalo",[])
   time.sleep(1800);continue

  live=api_get("https://v3.football.api-sports.io/fixtures?live=all",t=8)
  if live=="LIMIT":time.sleep(3600);continue
  if not live:time.sleep(60);continue

  cand_pre_75=[];cand_75=[]

  for g in live:
   try:
    m=g["fixture"]["status"]["elapsed"]or 0
    fid=g["fixture"]["id"]
    if not(15<=m<=79):continue

    d=stats_cache.get(fid)
    if not d or time.time()-d.get('time',0)>90:
     st=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}",t=8)
     if st and len(st)>=2:
      sot=get_stat(st[0]['statistics'],'Shots on Goal')+get_stat(st[1]['statistics'],'Shots on Goal')
      dang=get_stat(st[0]['statistics'],'Dangerous Attacks')+get_stat(st[1]['statistics'],'Dangerous Attacks')
      corn=get_stat(st[0]['statistics'],'Corner Kicks')+get_stat(st[1]['statistics'],'Corner Kicks')
      tot=get_stat(st[0]['statistics'],'Total Shots')+get_stat(st[1]['statistics'],'Total Shots')
      stats_cache[fid]={'sot':sot,'dang':dang,'corn':corn,'tot':tot,'time':time.time(),'gol':g['goals']['home']+g['goals']['away']}
      time.sleep(0.25)
     else:continue
    sot=stats_cache[fid]['sot'];dang=stats_cache[fid]['dang'];corn=stats_cache[fid]['corn'];tot=stats_cache[fid]['tot']

    # ========== CALCOLO % SEMPRE >85% ==========
    perc=0
    # 6 TIRI = MINIMO 85%
    if sot>=6 and dang>=40 and tot>=14:perc=95
    elif sot>=6 and dang>=35:perc=92
    elif sot>=6 and dang>=28:perc=90
    elif sot>=6 and dang>=20:perc=87
    elif sot>=6:perc=85
    # PRIMO TEMPO 3 TIRI
    elif sot>=3 and corn>=4 and dang>=20:perc=90
    elif sot>=3 and corn>=3 and dang>=15:perc=87
    elif sot>=3 and corn>=3:perc=85
    elif sot>=2 and corn>=4:perc=85
    else:perc=0

    if perc<85:continue # SE <85% NON MANDA NIENTE

    # ========== PRIMO TEMPO ==========
    # 10 MIN PRIMA PT: 15-24
    if 15<=m<=24 and fid not in avv_pre_pt and sot>=2 and corn>=2:
     gh=g['goals']['home'];ga=g['goals']['away']
     tg(f"👀 PREPARATI PT 10 MIN - {m}' TiriP:{sot} Ang:{corn} >{perc}%\n[{g['league']['country']} - {g['league']['name']}]\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}")
     avv_pre_pt.add(fid);salva("avv_pre_pt",list(avv_pre_pt))

    # GIOCALO PT: 30-45 - >85%
    if 30<=m<=45 and fid not in avv_pt and sot>=3 and corn>=3:
     gh=g['goals']['home'];ga=g['goals']['away']
     sq=g['teams']['home']['name'] if gh<=ga else g['teams']['away']['name']
     tg(f"🔥 PRIMO TEMPO {m}' TiriP:{sot} Ang:{corn} >{perc}%\n[{g['league']['country']} - {g['league']['name']}]\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\nNEXT: {sq}")
     avv_pt.add(fid);salva("avv_pt",list(avv_pt))

    # ========== SECONDO TEMPO 75' - 6 TIRI >85% ==========
    # 10 MIN PRIMA: 60-69 con 5-6 tiri ma gia >85%
    if 60<=m<=69 and fid not in avv_pre and sot>=5 and perc>=85:
     gh=g['goals']['home'];ga=g['goals']['away']
     tg(f"👀 PREPARATI 10 MIN - TRA POCO 75' - {m}' TiriP:{sot} >{perc}% Dang:{dang}\n[{g['league']['country']} - {g['league']['name']}]\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}")
     avv_pre.add(fid);salva("avv_pre",list(avv_pre))
     cand_pre_75.append({"min":m,"sot":sot,"perc":perc,"nazione":g['league']['country'],"match":f"{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}"})

    # GIOCALO 75': 70-79 con 6 tiri >85%
    if 70<=m<=79 and fid not in avv_giocalo and sot>=6 and perc>=85:
     gh=g['goals']['home'];ga=g['goals']['away']
     sq=g['teams']['home']['name'] if gh<=ga else g['teams']['away']['name']
     tg(f"🔥 GIOCALO 75' - {m}' TiriP:{sot} >{perc}% Dang:{dang}\n[{g['league']['country']} - {g['league']['name']}]\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\nNEXT: {sq} - 6 TIRI >{perc}%")
     avv_giocalo.add(fid);salva("avv_giocalo",list(avv_giocalo))
     cand_75.append({"min":m,"sot":sot,"perc":perc,"nazione":g['league']['country'],"camp":g['league']['name'],"match":f"{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}","next":sq})

   except:continue

  # TRIPLA CON >85%
  if len(cand_pre_75)>=3 and time.time()-ultima_pre_tripla>1800:
   txt=f"👀 PREPARATI TRIPLA TRA 10 MIN! {now.strftime('%H:%M')} >85%\n\n"
   for p in cand_pre_75[:3]:txt+=f"{p['min']}' >{p['perc']}% TiriP:{p['sot']} [{p['nazione']}]\n{p['match']}\n\n"
   tg(txt);ultima_pre_tripla=time.time()

  if len(cand_75)>=3 and time.time()-ultima_tripla>1800:
   if time.time()-ultima_pre_tripla>600:
    txt=f"🔥 TRIPLA 75' >85% 6 TIRI - {now.strftime('%H:%M')}\n\n"
    for i,p in enumerate(cand_75[:3],1):txt+=f"{i}. {p['min']}' >{p['perc']}% TiriP:{p['sot']} [{p['nazione']} - {p['camp']}]\n{p['match']}\nNEXT: {p['next']}\n\n"
    tg(txt);ultima_tripla=time.time()

  # GOL VINTO
  for g in live:
   fid=g["fixture"]["id"]
   if (fid in avv_giocalo or fid in avv_pt) and fid in stats_cache:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>stats_cache[fid].get('gol',tot):
     tg(f"✅ GOL VINTO! {g['fixture']['status']['elapsed']}' >85% [{g['league']['country']}] {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
     stats_cache[fid]['gol']=tot

  time.sleep(35)
 except Exception as e:print(f"ERR {e}",flush=True);time.sleep(30)
