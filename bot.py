import os,time,requests,json,threading
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

app=Flask(__name__)
@app.route('/')
def home(): return "BOT V19 OK"

def tg(m):
 try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":m},timeout=10)
 except: pass

def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_KEY},timeout=8)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except: return []

def salva(n,d):
 try: open(f"/tmp/{n}.json","w").write(json.dumps(d))
 except: pass
def leggi(n):
 try: return json.loads(open(f"/tmp/{n}.json","r").read())
 except: return None
def get_stat(a,n):
 for s in a:
  if s['type']==n:
   try: return int(str(s['value']).replace('%','')or 0)
   except: return 0
 return 0

# --- BOT LOOP IN BACKGROUND (1 solo Flask nel main) ---
avv_10=set(leggi("avv_10") or [])
avv_giocalo=set(leggi("avv_giocalo") or [])
avv_pt=set(leggi("avv_pt") or [])
stats_cache={}
ultimo_vivo=leggi("ultimo_vivo") or 0

def bot_loop():
 global ultimo_vivo
 time.sleep(2)
 tg("✅ BOT V19 PARTITO - 1 FLASK - >85%")
 while True:
  try:
   now=datetime.now(ITALY)
   if 0<=now.hour<10:
    time.sleep(600); continue

   if time.time() - ultimo_vivo > 900:
    lc=api_get("https://v3.football.api-sports.io/fixtures?live=all")
    if lc and lc!="LIMIT" and lc:
     tg(f"✅ VIVO V19 - {len(lc)} live - {now.strftime('%H:%M')} >85%")
     ultimo_vivo=time.time(); salva("ultimo_vivo",ultimo_vivo)

   live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
   if live=="LIMIT": time.sleep(3600); continue
   if not live: time.sleep(60); continue

   for g in live:
    try:
     m=g["fixture"]["status"]["elapsed"]or 0
     fid=g["fixture"]["id"]
     if not(15<=m<=79): continue
     d=stats_cache.get(fid)
     if not d or time.time()-d['time']>120:
      st=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
      if st and len(st)>=2:
       sot=get_stat(st[0]['statistics'],'Shots on Goal')+get_stat(st[1]['statistics'],'Shots on Goal')
       dang=get_stat(st[0]['statistics'],'Dangerous Attacks')+get_stat(st[1]['statistics'],'Dangerous Attacks')
       corn=get_stat(st[0]['statistics'],'Corner Kicks')+get_stat(st[1]['statistics'],'Corner Kicks')
       stats_cache[fid]={'sot':sot,'dang':dang,'corn':corn,'time':time.time()}
       time.sleep(0.3)
      else: continue
     sot=stats_cache[fid]['sot']; dang=stats_cache[fid]['dang']; corn=stats_cache[fid]['corn']

     perc=0
     if sot>=6 and dang>=40: perc=94
     elif sot>=6 and dang>=35: perc=92
     elif sot>=6 and dang>=28: perc=90
     elif sot>=6 and dang>=20: perc=87
     elif sot>=6: perc=85
     elif sot>=3 and corn>=4: perc=90
     elif sot>=3 and corn>=3: perc=87
     else: continue
     if perc<85: continue

     if 60<=m<=69 and fid not in avv_10 and sot>=5:
      tg(f"👀 PREPARATI 10 MIN 75' - {m}' TiriP:{sot} >{perc}%\n[{g['league']['country']}]\n{g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
      avv_10.add(fid); salva("avv_10",list(avv_10))

     if 70<=m<=79 and fid not in avv_giocalo and sot>=6:
      gh=g['goals']['home']; ga=g['goals']['away']
      if abs(gh-ga)>=2 and m>=75: continue
      sq=g['teams']['home']['name'] if gh<=ga else g['teams']['away']['name']
      tg(f"🔥 GIOCALO 75' - {m}' TiriP:{sot} >{perc}% Dang:{dang}\n[{g['league']['country']}]\n{g['teams']['home']['name']} {gh}-{ga} {g['teams']['away']['name']}\nNEXT: {sq}")
      avv_giocalo.add(fid); salva("avv_giocalo",list(avv_giocalo))
    except: continue
   time.sleep(40)
  except Exception as e: print(e); time.sleep(30)

threading.Thread(target=bot_loop,daemon=True).start()

# FLASK PARTE SOLO QUI, UNA VOLTA
if __name__=="__main__":
 app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
