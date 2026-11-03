import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
ROME=ZoneInfo("Europe/Rome")
is_paused=False
last_id=0
av_g={}
av_s=set()
av_s_first=set()
av_sfiga_score={}
av_builder={}

TOP={"Italy":135,"England":39,"Spain":140,"Germany":78,"France":61,"Netherlands":88,"Portugal":94,"Belgium":144,"Turkey":203,"Scotland":179,"Austria":218,"Switzerland":207,"Denmark":106,"Sweden":113,"Norway":103,"Poland":107}
def is_youth(n):
 b=n.lower()
 for x in ["u19","u21","u23","u17","women","youth","reserve"]:
  if x in b: return True
 return False

app=Flask(__name__)
@app.route("/")
def home():
 return "BOT V62 FIX OK",200

TAST=json.dumps({"keyboard":[["OVER 1.5 90% NAZIONI","OVER 3.5 WORLDWIDE"],["BOLLA EUROPA 33 NAZIONI"],["DOPPIA ALTA %"],["CALCIO D'ANGOLO +6"],["BAD BUILDER 1.82 WORLDWIDE"],["STATUS"],["ACCENDI","SPEGNI"],["CHIUDI MENU"]],"resize_keyboard":True})
TAST_C=json.dumps({"keyboard":[["APRI MENU"]],"resize_keyboard":True})

def tg(m,cid=None,keys=False,chiusa=False):
 try:
  cid=cid or CHAT
  if not cid or not BOT: return
  base="https://api.telegram.org/bot"+BOT
  pay={"chat_id":cid,"text":m,"parse_mode":"HTML"}
  if keys:
   pay["reply_markup"]=json.loads(TAST_C) if chiusa else json.loads(TAST)
  requests.post(base+"/sendMessage",json=pay,timeout=20)
 except Exception as e:
  print(e)

def api(url):
 try:
  r=requests.get(url,headers={"x-apisports-key":KEY},timeout=30)
  if r.status_code==429: return "LIMIT"
  return r.json().get("response",[])
 except Exception:
  return []

def get_sfigata(fid):
 try:
  data=api(f"https://v3.football.api-sports.io/odds?fixture={fid}")
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:2]:
   for bet in book.get("bets",[]):
    if bet.get("name")=="Match Winner":
     q={}
     for v in bet.get("values",[]):
      try: q[v.get("value")]=float(v.get("odd"))
      except: pass
     h=q.get("Home",0); a=q.get("Away",0)
     if h>=4.5 and h>a and a<=1.8: return ("HOME",h,"AWAY",a)
     if a>=4.5 and a>h and h<=1.8: return ("AWAY",a,"HOME",h)
  return None
 except Exception:
  return None

def get_over_odd(fid):
 try:
  data=api(f"https://v3.football.api-sports.io/odds?fixture={fid}")
  if not data or data=="LIMIT": return None
  for book in data[0].get("bookmakers",[])[:3]:
   for bet in book.get("bets",[]):
    if "Over/Under" in bet.get("name",""):
     for v in bet.get("values",[]):
      if "Over 1.5" in v.get("value",""):
       try: return float(v.get("odd"))
       except: pass
 except Exception:
  pass
 return None

def get_last10(team_id):
 try:
  data=api(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT")
  if not data or data=="LIMIT": return "LIMIT"
  if len(data)<5: return None
  c15=0
  for f in data:
   gh=f.get("goals",{}).get("home") or 0; ga=f.get("goals",{}).get("away") or 0
   if gh+ga>=2: c15+=1
  return c15/len(data)*100
 except Exception:
  return None

def get_best90(hid,aid):
 try:
  s1=get_last10(hid)
  if s1=="LIMIT": return "LIMIT"
  time.sleep(0.4)
  s2=get_last10(aid)
  if s2=="LIMIT": return "LIMIT"
  if s1 is None or s2 is None: return None
  avg=(s1+s2)/2
  return avg if avg>=90 else None
 except Exception:
  return None

def get_corner_avg
