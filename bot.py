import os,time,requests,threading,json,fcntl
from flask import Flask
from datetime import datetime,timezone,timedelta,date
from zoneinfo import ZoneInfo
from urllib.parse import quote
BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
KEY=os.getenv("API_FOOTBALL_KEY")
ODDS_KEY=os.getenv("ODDS_API_KEY")
ITALY=timezone(timedelta(hours=2))
ROME=ZoneInfo("Europe/Rome")
is_paused=False
last_id=0
av_g={}
av_s=set()
av_s_first=set()
av_sfiga_score={}
av_sfiga_sent=set()
seen=set()
TOP={
"Italy":135,"England":39,"Spain":140,"Germany":78,
"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,
"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,
"Denmark":106,"Sweden":113,"Norway":103,"Poland":107,
"Czech Republic":345,"Croatia":210,"Serbia":286,"Greece":197,
"Romania":283,"Bulgaria":172,"Hungary":271,"Slovakia":332,
"Slovenia":373,"Ireland":344,"Wales":110,"Finland":244,
"Iceland":164,"Cyprus":318,"Malta":389,"Luxembourg":261,
"Belarus":116,"Russia":235
}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b:
   return True
 return False
app=Flask(__name__)
@app.route("/")
def home():
 return "BOT V76 FULL + OVER 1.5 90% + BUILDER WORLDWIDE + BASKET HANDICAP 12+",200
def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT:
   return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except Exception as e:
  print(e)
def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429:
   return "LIMIT"
  return r.json().get("response",[])
 except:
  return []
def goldbet_button(home,away):
 u=f"https://www.goldbet.it/qs/sport/ricerca/{quote(home+' '+away)}"
 return {"text":"Goldbet - Vai alla partita","url":u}
def tg_inline(m,rows,cid=None):
 try:
  cid=cid or CHAT
  if not cid or not BOT:
   return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if rows:
   kb=[[r] for r in rows]
   pay["reply_markup"]=json.dumps({"inline_keyboard":kb})
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except Exception as e:
  print(e)
def get_sot(fid):
 st=api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}")
 if st=="LIMIT" or not st or len(st)<2:
  return None
 sot=0
 for s in st:
  if not isinstance(s,dict):
   continue
  for x in s.get("statistics",[]):
   if "Shots on Goal" in (x.get("type") or ""):
    try:
     sot+=int(str(x.get("value") or 0))
    except:
     pass
 return sot
def get_sfigata(fid):
 try:
  u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
  data=api(u)
  if not data or data=="LIMIT":
   return None
  for book in data[0].get("bookmakers",[])[:2]:
   for bet in book.get("bets",[]):
    if bet.get("name")=="Match Winner":
     q={}
     for v in bet.get("values",[]):
      try:
       q[v.get("value")]=
