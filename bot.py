import os
import time
import requests
import threading
import json
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT = os.getenv('BOT_TOKEN')
CHAT = os.getenv('CHAT_ID')
KEY = os.getenv('API_FOOTBALL_KEY')
ITALY = timezone(timedelta(hours=2))
last_id = 0

LEAGUES = {'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}

TOP = {'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':106,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}

app = Flask(__name__)
@app.route('/')
def home():
    return 'BOT V49 FINAL COMPLETO OK',200

TAST = json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA 90%"],["BOLLA EUROPA 33 NAZIONI"],["STATUS"]],"resize_keyboard":True})

def tg(m,cid=None,keys=False):
    try:
        cid = cid or CHAT
        if not BOT or not cid:
            return
        base = 'https://api.telegram.org/bot'+BOT
        pay = {'chat_id':cid,'text':m,'parse_mode':'HTML'}
        if keys:
            pay['reply_markup']=json.loads(TAST)
        requests.post(base+'/sendMessage',json=pay,timeout=25)
    except:
        pass

def api(url):
    try:
        if not KEY:
            return []
        r = requests.get(url,headers={'x-apisports-key':KEY},timeout=35)
        if r.status_code == 429:
            return []
        return r.json().get('response',[])
    except:
        return []

def get_dc(fid):
    try:
        data = api('https://v3.football.api-sports.io/odds?fixture='+str(fid))
        if not data:
            return None
        for book in data[0].get('bookmakers',[])[:2]:
            for bet in book.get('bets',[]):
                if 'Double Chance' in bet.get('name',''):
                    best = None
                    best_odd = 10.0
                    for v in bet.get('values',[]):
                        try:
                            o = float(v['odd'])
                            if o < best_odd:
                                best_odd = o
                                best = v['value']
                        except:
                            continue
                    if best:
                        prob = int(100/best_odd) if best_odd else 0
                        if 'Home/Draw' in best:
                            return f"1X @ {best_odd:.2f} ({prob}%)",prob
                        if 'Draw/Away' in best:
                            return f"X2 @ {best_odd:.2f} ({prob}%)",prob
                        if 'Home/Away' in best:
                            return f"12 @ {best_odd:.2f} ({prob}%)",prob
    except:
        pass
    return None

def get_today():
    today = datetime.now(ITALY).strftime('%Y-%m-%d')
    return api('https://v3.football.api-sports.io/fixtures?date='+today+'&timezone=Europe/Rome')

def get_corner(fid,tid):
    try:
        st = api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
        if not st:
            return None
        for team_stat in st:
            if team_stat['team']['id']!= tid:
                continue
            for s in team_stat.get('statistics',[]):
                if 'Corner' in s.get('type',''):
                    if s['value'] is not None:
                        return s['value']
    except:
        pass
    return None

def run_bolla(cid=None):
    data = get_today()
    sel = []
    for country, top_id in TOP.items():
        for f in data:
            if f['league']['id']!= top_id:
                continue
            if f['league']['country']!= country:
                continue
            fid = f['fixture']['id']
            ora = f['fixture']['date'][11:16]
            home = f['teams']['home']['name']
            away = f['teams']['away']['name']
            res = get_dc(fid)
            dc = res[0] if res else "1X @ 1.25"
            if res:
                time.sleep(0.35)
            sel.append(f"{ora} {home} vs {away} -> {dc} ({country})")
            break
        if len(sel) >= 33:
            break
    if sel:
        out = "".join([f"{i+1}. {m}\n" for i,m in enumerate(sel)])
        tg(f"BOLLA EUROPA {len(sel)} NAZIONI\n\n{out}",cid,True)
    else:
        tg("Oggi nessuna TOP League - 0 partite",cid,True)

def run_doppia(cid=None):
    data = get_today()
    out = []
    for f in data:
        if f['league']['country'] not in TOP:
            continue
        if f['league']['id']!= TOP[f['league']['country']]:
            continue
        res = get_dc(f['fixture']['id'])
        if not res:
            continue
        if res[1] < 80:
            continue
        ora = f['fixture']['date'][11:16]
        home = f['teams']['home']['name']
        away = f['teams']['away']['name']
        out.append((res[1],f"{ora} {home} vs {away} -> {res[0]}"))
        time.sleep(0.35)
    if out:
        out.sort(key=lambda x: x[0], reverse=True)
        msg = "".join([f"{i+1}. {m}\n" for i,(p,m) in enumerate(out)])
        tg(f"DOPPIA 90% - {len(out)} PARTITE\n\n{msg}",cid,True)
    else:
        tg("Nessuna DOPPIA 90% oggi",cid,True)

def media(lid,name):
    txt = name.upper()+"\n"+datetime.now(ITALY).strftime("%d/%m %H:%M")+"\n10 ULTIME - GOAL + CORNER\n\n"
    teams = api(f'https://v3.football.api-sports.io/teams?league={lid}&season=2024')
    if not teams:
        return 'Errore API o Limite'
    for t in teams[:14]:
        tid = t['team']['id']
        tname = t['team']['name']
        last = api(f'https://v3.football.api-sports.io/fixtures?team={tid}&last=10&season=2024')
        gf=gs=tot=c=0
        ctot=cc=0
        for p in last:
            gh = p['goals']['home']
            ga = p['goals']['away']
            if gh is None:
                continue
            fid = p['fixture']['id']
            if p['teams']['home']['id'] == tid:
                gf+=gh;gs+=ga
            else:
                gf+=ga;gs+=gh
            tot+=gh+ga
            c+=1
            cor = get_corner(fid,tid)
            if cor is not None:
                ctot+=cor
                cc+=1
            time.sleep(0.25)
        if c==0:
            continue
        avg_c = ctot/cc if cc>0 else 0
        txt+=f"{tname}:\n Goal {gf}F/{gs}S Diff {gf-gs:+} Med {tot/c:.2f}\n Corner Tot {ctot} Med {avg_c:.1f} ({cc}/10)\n\n"
        time.sleep(0.25)
    return txt

def poll():
    global last_id
    try:
        if BOT:
            requests.get('https://api.telegram.org/bot'+BOT+'/deleteWebhook?drop_pending_updates=true',timeout=10)
    except:
        pass
    while True:
        try:
            if not BOT:
                time.sleep(60)
                continue
            base = 'https://api.telegram.org/bot'+BOT
            r = requests.get(base+f'/getUpdates?offset={last_id+1}&timeout=20',timeout=35).json()
            if r.get('ok'):
                for u in r.get('result',[]):
                    last_id = u['update_id']
                    msg = u.get('message',{})
                    txt = (msg.get('text') or '').strip()
                    low = txt.lower()
                    cid = msg.get('chat',{}).get('id')
                    if not txt:
                        continue
                    if 'doppia' in low:
                        run_doppia(cid)
                    elif 'bolla' in low:
                        run_bolla(cid)
                    elif 'status' in low:
                        tg('BOT V49 FINAL COMPLETO OK - 10G + CORNER + DOPPIA + BOLLA',cid,True)
                    else:
                        for k in LEAGUES:
                            if k.lower() == low:
                                tg(media(LEAGUES[k],k),cid,True)
        except:
            pass
        time.sleep(2)

threading.Thread(target=poll,daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
