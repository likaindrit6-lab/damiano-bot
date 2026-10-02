import os,time,requests,threading
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

app=Flask(__name__)
@app.route('/')
def home():return "BOT OK"

def run_flask():
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_flask,daemon=True).start()

def tg(m):
 try:
  requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":m,"parse_mode":"HTML"},timeout=25)
 except:pass

def api_get(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=30)
  if r.status_code==429:return "LIMIT"
  return r.json().get("response",[])
 except:return []

def get_stat(a,n):
 for s in a:
  if s.get('type')==n:
   try:
    v=s.get('value')
    if v is None:return 0
    return int(str(v).replace('%','').strip()or 0)
   except:return 0
 return 0

def get_flag(p):
 m={"Italy":"🇮🇹","England":"🇬🇧","Spain":"🇪🇸","Germany":"🇩🇪","France":"🇫🇷","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪","Turkey":"🇹🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","USA":"🇺🇸"}
 return m.get(p,f"[{p.upper()}]")

av_g,av_s,pre,pre1,cache={},set(),set(),set(),{}
print("BOT V5.1 FIX - NO SPAM AVVIATO",flush=True)

while True:
 try:
  now=datetime.now(ITALY)
  if 0<=now.hour<10:
   if now.hour==0:
    av_s.clear();pre.clear();pre1.clear();av_g.clear();cache.clear()
   time.sleep(1800);continue
  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT":
   time.sleep(3600);continue
  if not live:
   time.sleep(90);continue
  for g in live:
   fid=g["fixture"]["id"];st=g["fixture"]["status"]["short"];m=g["fixture"]["status"]["elapsed"]
   if m is None or fid in av_s:continue
   home=g['teams']['home']['name'];away=g['teams']['away']['name'];gh=g['goals']['home'];ga=g['goals']['away'];paese=g['league']['country'];lega=g['league']['name'];flag=get_flag(paese);pref=f"{flag} {paese.upper()} - {lega}"
   def tiri():
    d=cache.get(fid)
    if not d or time.time()-d.get('time',0)>300:
     s=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
     if s and len(s)>=2:
      sot=get_stat(s[0]['statistics'],'Shots on Goal')+get_stat(s[1]['statistics'],'Shots on Goal');cache[fid]={'sot':sot,'time':time.time()};time.sleep(0.6);return sot
     return d.get('sot',0) if d else 0
    return d.get('sot',0)
   if st=="HT" and fid not in pre1:
    so=tiri()
    if so>=3:
     tg(f"FINE 1T 45' {pref} | Tiri:{so} | {home} {gh}-{ga} {away}")
    pre1.add(fid)
   if 45<=(m or 0)<=69 and fid not in pre:
    so=tiri()
    if so>=5:
     tg(f"PREPARATI {m}' {pref} | Tiri:{so} | {home} {gh}-{ga} {away}");pre.add(fid)
   if 70<=(m or 0)<=92:
    so=tiri()
    if so>=6:
     sq=home if gh<=ga else away;tg(f"GIOCALO {m}' >85% {pref} | Tiri:{so} | {home} {gh}-{ga} {away} | NEXT {sq}");av_s.add(fid);av_g[fid]=gh+ga
  for g in live:
   fid=g["fixture"]["id"]
   if fid in av_g:
    tot=g["goals"]["home"]+g["goals"]["away"]
    if tot>av_g[fid]:
     flag=get_flag(g['league']['country']);tg(f"🟢 GOAL VINTO! {flag} {g['league']['country'].upper()} - {g['league']['name']} | {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}");del av_g[fid]
  time.sleep(90)
 except:
  time.sleep(20)
