import os,time,requests,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))
app=Flask(__name__)
@app.route('/')
def home():return "BOT OK - FIX ANTI-SPAM"
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
  if"over 0.5"in t:return(gh+ga)>=1
  if"over 1.5"in t:return(gh+ga)>=2
  if"home"in t:return gh>ga
  if"x2"in t:return ga>=gh
  return None
 except:return None

# ANTI-SPAM: manda messaggio avvio solo ogni 2 ore
ult = leggi_file("ult_avvio")
if not ult or time.time()-ult.get("t",0)>7200:
 tg("✅ BOT FIXATO ANTI-SPAM - PROG SOLO OVER + MADRE/Q5/Q20 alle 14:00")
 salva_file("ult_avvio",{"t":time.time()})

avvisati_gol={};avvisati_squadra=set();preavvisati=set();preavvisati_1t=set();stats_cache={};bombe_fatte=False;madre_fatta=False;ultimo_hb=0;ultima_schedina=0;ultima_pre_schedina=0;ultimo_check_vincita=0
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

import threading
threading.Thread(target=lambda:app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()

while True:
 try:
  now=datetime.now(ITALY)
  if 0<=now.hour<7:
   if now.hour==0:bombe_fatte=False;madre_fatta=False;avvisati_squadra.clear();preavvisati.clear();preavvisati_1t.clear();avvisati_gol.clear();stats_cache.clear()
   time.sleep(1800);continue
  if time.time()-ultimo_hb>3600:
   lc=api_get("https://v3.football.api-sports.io/fixtures?live=all")
   if lc=="LIMIT":time.sleep(3600);continue
   tg(f"✅ VIVO - {len(lc)} live - {now.strftime('%H:%M:%S')}")
   ultimo_hb=time.time()

  # PROG FIXATA - SOLO OVER
  if not bombe_fatte and now.hour>=7 and now.hour<9:
   fix=api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
   fix=[x for x in fix if x['fixture']['status']['short']=='NS']
   cand_prog=[]
   for g in fix[:90]:
    odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={g['fixture']['id']}")
    if odds=="LIMIT":time.sleep(3600);continue
    if not odds:time.sleep(0.2);continue
    for o in odds:
     for bk in o.get("bookmakers",[])[:2]:
      for bet in bk.get("bets",[]):
       bn=bet["name"].lower()
       if "over/under" not in bn:continue
       if "second half" in bn or "first half" in bn:continue
       for v in bet["values"]:
        try:
         val=v["value"].lower()
         if "over 0.5" in val or "over 1.5" in val:
          q=float(v["odd"])
          if 1.08<=q<=1.20:
           ora=datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY).strftime('%H:%M')
           base={"id":g['fixture']['id'],"match":f"{g['teams']['home']['name']} vs {g['teams']['away']['name']}","ora":ora,"quota":q,"tipo":v["value"]}
           cand_prog.append(base)
        except:pass
    time.sleep(0.4)
   cand_prog=sorted(cand_prog,key=lambda x:x['quota'])
   visti=set();filtr=[]
   for c in cand_prog:
    if c['id']not in visti:filtr.append(c);visti.add(c['id'])
   finale=[];tot=1.0
   for c in filtr:
    if tot*c['quota']<=1.65:finale.append(c);tot*=c['quota']
    if tot>=1.50:break
   if finale:
    salva_file(f"prog_{now.strftime('%Y-%m-%d')}",finale)
    sett=leggi_file("prog_settimanale")or[]
    sett.append({"data":now.strftime('%Y-%m-%d'),"partite":finale,"quota":tot})
    salva_file("prog_settimanale",sett)
    txt2=f"📈 PROG {now.strftime('%d/%m')} Giorno {len(sett)}/7 - Q{round(tot,2)} {len(finale)} SOLO OVER\n\n"
    for i,b in enumerate(finale,1):txt2+=f"{i}. {b['ora']} {b['match']} {b['tipo']} Q{b['quota']}\n"
    tg(txt2)
   bombe_fatte=True

  # MADRE + Q5 + Q20 ALLE 14:00
  if not madre_fatta and now.hour>=14 and now.hour<15:
   monday = now - timedelta(days=now.weekday())
   bombe=[];madre_save=[];visti_madre=set()
   for i in range(7):
    giorno = (monday + timedelta(days=i)).strftime('%Y-%m-%d')
    fix=api_get(f"https://v3.football.api-sports.io/fixtures?date={giorno}")
    fix=[x for x in fix if x['fixture']['status']['short']=='NS']
    for g in fix:
     if len(bombe)>=30:break
     if g['fixture']['id'] in visti_madre:continue
     odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={g['fixture']['id']}")
     if odds=="LIMIT":time.sleep(3600);continue
     if not odds:continue
     for o in odds:
      for bk in o.get("bookmakers",[])[:3]:
       for bet in bk.get("bets",[]):
        if "Over/Under" in bet["name"] and "second half" not in bet["name"].lower():
         for v in bet["values"]:
          try:
           if "over 1.5" in v["value"].lower():
            q=float(v["odd"])
            if 1.02 <= q <= 1.25 and g['fixture']['id'] not in visti_madre:
             ora_day=datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY).strftime('%d/%m %H:%M')
             bombe.append(f"{ora_day} {g['teams']['home']['name']} vs {g['teams']['away']['name']} OVER 1.5 Q{q}\n")
             madre_save.append({"id":g['fixture']['id'],"match":f"{g['teams']['home']['name']} vs {g['teams']['away']['name']}","ora":ora_day,"quota":q,"tipo":"Over 1.5"})
             visti_madre.add(g['fixture']['id'])
          except:pass
       if len(bombe)>=30:break
      if len(bombe)>=30:break
     time.sleep(0.25)
    if len(bombe)>=30:break
   if bombe:
    txt=f"💣 MADRE 30 - {len(bombe)} PARTITE\n\n"
    for i,b in enumerate(bombe,1):txt+=f"{i}. {b}\n"
    tg(txt);salva_file(f"madre_{now.strftime('%Y-%m-%d')}",madre_save)

   fix_oggi=api_get(f"https://v3.football.api-sports.io/fixtures?date={now.strftime('%Y-%m-%d')}")
   fix_oggi=[x for x in fix_oggi if x['fixture']['status']['short']=='NS']
   cand=[]
   for g in fix_oggi[:80]:
    odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={g['fixture']['id']}")
    if odds=="LIMIT":time.sleep(3600);continue
    if not odds:continue
    for o in odds:
     for bk in o.get("bookmakers",[])[:2]:
      for bet in bk.get("bets",[]):
       if "Over/Under" in bet["name"] and "second half" not in bet["name"].lower():
        for v in bet["values"]:
         try:
          if "over 1.5" in v["value"].lower() or "over 0.5" in v["value"].lower():
           q=float(v["odd"])
           if 1.08<=q<=1.30:
            ora=datetime.fromisoformat(g['fixture']['date'].replace('Z','+00:00')).astimezone(ITALY).strftime('%H:%M')
            cand.append({"id":g['fixture']['id'],"match":f"{g['teams']['home']['name']} vs {g['teams']['away']['name']}","ora":ora,"quota":q,"tipo":v["value"]})
         except:pass
    time.sleep(0.2)
   cand=sorted(cand,key=lambda x:x['quota'])
   v=set();cf=[]
   for c in cand:
    if c['id'] not in v:cf.append(c);v.add(c['id'])
   cand=cf[:13]
   if len(cand)>=7:
    q5=cand[:7];tot5=1
    for c in q5:tot5*=c['quota']
    txt5=f"🔥 Q5 - Q{round(tot5,2)}\n\n"
    for i,b in enumerate(q5,1):txt5+=f"{i}. {b['ora']} {b['match']} {b['tipo']} Q{b['quota']}\n"
    tg(txt5);salva_file(f"q5_{now.strftime('%Y-%m-%d')}",q5)
   if len(cand)>=13:
    q20=cand[:13];tot20=1
    for c in q20:tot20*=c['quota']
    txt20=f"💥 Q20 - Q{round(tot20,2)}\n\n"
    for i,b in enumerate(q20,1):txt20+=f"{i}. {b['ora']} {b['match']} {b['tipo']} Q{b['quota']}\n"
    tg(txt20);salva_file(f"q20_{now.strftime('%Y-%m-%d')}",q20)
   madre_fatta=True

  if time.time() - ultimo_check_vincita > 1800:
   ultimo_check_vincita = time.time()
   for nome_file in [f"prog_{now.strftime('%Y-%m-%d')}", f"madre_{now.strftime('%Y-%m-%d')}", f"q5_{now.strftime('%Y-%m-%d')}", f"q20_{now.strftime('%Y-%m-%d')}"]:
    data = leggi_file(nome_file)
    if not data: continue
    if leggi_file(f"esito_{nome_file}"): continue
    risultati = []
    for p in data:
     r = check_vincita(p['id'], p['tipo'])
     risultati.append(r)
     time.sleep(0.3)
    if all(r is not None for r in risultati):
     vinte = sum(1 for r in risultati if r == True)
     tag=nome_file.split('_')[0].upper()
     if vinte==len(risultati):tg(f"✅✅ {tag} HAI VINTO!!! {vinte}/{len(risultati)} 💰")
     else:tg(f"❌ {tag} HAI PERSO - {vinte}/{len(risultati)}")
     salva_file(f"esito_{nome_file}", {"vinte": vinte})

  live=api_get("https://v3.football.api-sports.io/fixtures?live=all")
  if live=="LIMIT":time.sleep(3600);continue
  if len(live)==0:time.sleep(180);continue
  time.sleep(60)
 except Exception as e:print(f"ERR {e}",flush=True);time.sleep(30)
