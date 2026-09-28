import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
app=Flask(__name__)
@app.route('/')
def home():return "BOT V7 DAMI OK"
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

def salva_file(nome,data):
 try:
  with open(f"/tmp/{nome}.json","w")as f:json.dump(data,f)
 except:pass
def leggi_file(nome):
 try:
  with open(f"/tmp/{nome}.json","r")as f:return json.load(f)
 except:return None

def get_stat(arr,nome):
 for s in arr:
  if s['type']==nome:
   try:return int(str(s['value']).replace('%','')or 0)
   except:return 0
 return 0

def thread_vivo():
 u=0
 while True:
  try:
   now=datetime.now(ITALY)
   if 0<=now.hour<10:time.sleep(1800);continue
   if time.time()-u>900:
    lc=api_get("https://v3.football.api-sports.io/fixtures?live=all",t=8)
    if lc!="LIMIT" and lc:tg(f"✅ VIVO V7 - {len(lc)} live - {now.strftime('%H:%M')}");u=time.time()
   time.sleep(120)
  except:time.sleep(60)
threading.Thread(target=thread_vivo,daemon=True).start()
time.sleep(2)
tg("✅ BOT V7 PARTITO - BASE DAMI - 20 + MADRE SETT + TRIPLA 70")

bombe_fatte=False;madre_sett_fatta=False
avvisati_pre=set();avvisati_giocalo=set();avvisati_gol={}
stats_cache={};ultima_tripla=0;ultima_pre_tripla=0

while True:
 try:
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:bombe_fatte=False;madre_sett_fatta=False;avvisati_pre.clear();avvisati_giocalo.clear();avvisati_gol.clear();stats_cache.clear()
   time.sleep(1800);continue

  # PUNTO 1 - SCHEDINA 20 GIORNALIERA 10-23:59 MONDO >85%
  if not bombe_fatte and now.hour>=10 and now.hour<13:
   fix=api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}",t=10)
   fix=[x for x in fix if x['fixture']['status']['short']=='NS']
   sched20=[]
   for g in fix:
    if len(sched20)>=20:break
    ora_ita=datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY)
    if not(10<=ora_ita.hour<=23):continue
    fid=g['fixture']['id']
    odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}",t=6)
    if odds=="LIMIT":time.sleep(3600);continue
    if not odds:time.sleep(0.15);continue
    for o in odds:
     for bk in o.get("bookmakers",[])[:1]:
      for bet in bk.get("bets",[]):
       for v in bet["values"]:
        try:
         q=float(v["odd"]);perc=(1/q)*100
         if perc>=85 and q<=1.30:
          sched20.append({"ora":ora_ita.strftime('%H:%M'),"nazione":g['league']['country'],"camp":g['league']['name'],"match":f"{g['teams']['home']['name']} vs {g['teams']['away']['name']}","tipo":f"{bet['name']} {v['value']}","quota":q,"perc":round(perc,1)});break
        except:pass
      if len(sched20)>=20:break
     if len(sched20)>=20:break
    time.sleep(0.2)
   if sched20:
    txt=f"💣 SCHEDINA 20 - {now.strftime('%d/%m')} 10-23:59 MONDO >85%\n\n"
    for i,p in enumerate(sched20,1):txt+=f"{i}. {p['ora']} [{p['nazione']} - {p['camp']}]\n{p['match']}\n{p['tipo']} Q{p['quota']} >{p['perc']}%\n\n"
    tg(txt)
   bombe_fatte=True

  # PUNTO 2 - MADRE SETTIMANALE LUN-DOM 30 PARTITE >90%
  if not madre_sett_fatta and now.weekday()==0 and now.hour>=10 and now.hour<13:
   madre=leggi_file("madre_sett")or[]
   for gg in range(0,7):
    data_scan=(now+timedelta(days=gg)).strftime('%Y-%m-%d')
    fix=api_get(f"https://v3.football.api-sports.io/fixtures?date={data_scan}",t=10)
    fix=[x for x in fix if x['fixture']['status']['short']=='NS']
    for g in fix:
     if len(madre)>=30:break
     fid=g['fixture']['id']
     if any(x['id']==fid for x in madre):continue
     odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}",t=6)
     if not odds:continue
     for o in odds:
      for bk in o.get("bookmakers",[])[:1]:
       for bet in bk.get("bets",[]):
        for v in bet["values"]:
         try:
          q=float(v["odd"]);perc=(1/q)*100
          if perc>=90:
           bn=bet["name"].lower();val=v["value"].lower()
           ok=False
           if "winner" in bn:ok=True
           if "double" in bn:ok=True
           if "0.5" in val or "1.5" in val:ok=True
           if "to score" in bn:ok=True
           if ok:
            ora_ita=datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY)
            madre.append({"giorno":ora_ita.strftime('%a %d/%m %H:%M'),"nazione":g['league']['country'],"camp":g['league']['name'],"match":f"{g['teams']['home']['name']} vs {g['teams']['away']['name']}","tipo":f"{bet['name']} {v['value']}","quota":q,"perc":round(perc,1),"id":fid});break
         except:pass
      if len(madre)>=30:break
     time.sleep(0.15)
     if len(madre)>=30:break
    if len(madre)>=30:break
   if madre:
    salva_file("madre_sett",madre)
    txt=f"💣 MADRE SETTIMANALE LUN-DOM {len(madre)}/30 >90%\n\n"
    for i,p in enumerate(madre,1):txt+=f"{i}. {p['giorno']} [{p['nazione']} - {p['camp']}]\n{p['match']}\n{p['tipo']} Q{p['quota']} >{p['perc']}%\n\n"
    tg(txt)
   madre_sett_fatta=True

  # PUNTO 3 - TRIPLA 70' >90% 6 TIRI + PRE 10 MIN - OGNI 30 MIN
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all",t=8)
  if live=="LIMIT":time.sleep(3600);continue
  if not live:time.sleep(60);continue
  cand_70=[];cand_pre=[]
  for g in live:
   try:
    m=g["fixture"]["status"]["elapsed"]or 0
    if m<55 or m>92:continue
    fid=g["fixture"]["id"]
    d=stats_cache.get(fid)
    if not d or time.time()-d.get('time',0)>90:
     st=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}",t=8)
     if st and len(st)>=2:
      sot=get_stat(st[0]['statistics'],'Shots on Goal')+get_stat(st[1]['statistics'],'Shots on Goal')
      dang=get_stat(st[0]['statistics'],'Dangerous Attacks')+get_stat(st[1]['statistics'],'Dangerous Attacks')
      stats_cache[fid]={'sot':sot,'dang':dang,'time':time.time(),'gol':g['goals']['home']+g['goals']['away']}
      time.sleep(0.25)
     else:continue
    sot=stats_cache[fid]['sot'];dang=stats_cache[fid]['dang']
    if sot<6:continue
    perc=0
    if sot>=6 and dang>=40:perc=95
    elif sot>=6 and dang>=35:perc=93
    elif sot>=6 and dang>=30:perc=91
    elif sot>=6 and dang>=25:perc=90
    if perc>=90:
     if 70<=m<=92:cand_70.append({"min":m,"sot":sot,"dang":dang,"perc":perc,"nazione":g['league']['country'],"camp":g['league']['name'],"match":f"{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}","next":g['teams']['home']['name'] if g['goals']['home']<=g['goals']['away'] else g['teams']['away']['name'],"id":fid})
     elif 55<=m<=69:cand_pre.append({"min":m,"sot":sot,"perc":perc,"nazione":g['league']['country'],"camp":g['league']['name'],"match":f"{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}"})
    # GIOCALO SINGOLO
    if 70<=m<=92 and fid not in avvisati_giocalo and sot>=6:
     tg(f"🔥 GIOCALO {m}' TiriP:{sot} >{perc}%\n[{g['league']['country']} - {g['league']['name']}]\n{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}\nNEXT: {g['teams']['home']['name'] if g['goals']['home']<=g['goals']['away'] else g['teams']['away']['name']}")
     avvisati_giocalo.add(fid)
   except:continue

  if len(cand_pre)>=3 and time.time()-ultima_pre_tripla>1800:
   txt=f"👀 PREPARATI TRIPLA - TRA 10 MIN! {now.strftime('%H:%M')} >90% 6 TIRI\n\n"
   for p in cand_pre[:3]:txt+=f"{p['min']}' >{p['perc']}% TiriP:{p['sot']} [{p['nazione']} - {p['camp']}]\n{p['match']}\n\n"
   tg(txt);ultima_pre_tripla=time.time()

  if len(cand_70)>=3 and time.time()-ultima_tripla>1800:
   txt=f"🔥 TRIPLA 70' >90% 6 TIRI - {now.strftime('%H:%M')}\n\n"
   for i,p in enumerate(cand_70[:3],1):txt+=f"{i}. {p['min']}' >{p['perc']}% TiriP:{p['sot']} [{p['nazione']} - {p['camp']}]\n{p['match']}\nNEXT: {p['next']}\n\n"
   tg(txt);ultima_tripla=time.time()

  # GOL VINTO
  for g in live:
   fid=g["fixture"]["id"]
   if fid in avvisati_giocalo and fid in stats_cache:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>stats_cache[fid].get('gol',tot):tg(f"✅ GOL VINTO! [{g['league']['country']}] {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");stats_cache[fid]['gol']=tot

  time.sleep(30)
 except Exception as e:print(f"ERR {e}",flush=True);time.sleep(30)
