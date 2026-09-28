import os,time,requests,threading
from flask import Flask
from datetime import datetime,timezone,timedelta

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
API_KEY=os.getenv("API_FOOTBALL_KEY")
ITALY=timezone(timedelta(hours=2))

app=Flask(__name__)
@app.route('/')
def home():return "V3 DOPPIO THREAD OK"
threading.Thread(target=lambda:app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()

def tg(m):
    print(m,flush=True)
    try:requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":m,"parse_mode":"HTML"},timeout=15)
    except:pass

def api_get(url,timeout=8):
    try:
        r=requests.get(url,headers={"x-apisports-key":API_KEY},timeout=timeout)
        if r.status_code==429:return "LIMIT"
        return r.json().get("response",[])
    except:return []

avvisati=set();gol_attesa={};cache={}

def get_val(arr,nome):
    for s in arr:
        if s['type']==nome:
            try:return int(str(s['value']).replace('%','')or 0)
            except:return 0
    return 0

# --- THREAD 1: CHECK CHE NON DORME MAI ---
def thread_check():
    while True:
        try:
            now=datetime.now(ITALY)
            if 0<=now.hour<10:
                print(f"NOTTE {now.strftime('%H:%M')}",flush=True)
                time.sleep(1800);continue
            live=api_get("https://v3.football.api-sports.io/fixtures?live=all",timeout=8)
            if live=="LIMIT":
                print("LIMIT CHECK",flush=True);time.sleep(3600);continue
            print(f"CHECK {now.strftime('%H:%M')} - {len(live)} live",flush=True)
            if now.minute%30==0: # VIVO ogni 30 min
                tg(f"✅ VIVO V3 - {len(live)} live - {now.strftime('%H:%M')}")
            time.sleep(300)
        except Exception as e:
            print(f"ERR CHECK {e}",flush=True);time.sleep(30)

# --- THREAD 2: CACCIATORE PARTITE ---
def thread_caccia():
    time.sleep(10)
    while True:
        try:
            now=datetime.now(ITALY)
            if 0<=now.hour<10:time.sleep(1800);continue
            live=api_get("https://v3.football.api-sports.io/fixtures?live=all",timeout=8)
            if live=="LIMIT" or not live:time.sleep(300);continue

            for g in live[:8]: # solo prime 8 per non intasare
                try:
                    m=g["fixture"]["status"]["elapsed"]or 0
                    if m<65 or m>90:continue
                    fid=g["fixture"]["id"]
                    if fid in avvisati:continue

                    home=g['teams']['home']['name'];away=g['teams']['away']['name']
                    gh=g['goals']['home'];ga=g['goals']['away']

                    # stats veloci con timeout corto
                    st=api_get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}",timeout=5)
                    if not st or len(st)<2:continue

                    sot=get_val(st[0]['statistics'],'Shots on Goal')+get_val(st[1]['statistics'],'Shots on Goal')
                    dang=get_val(st[0]['statistics'],'Dangerous Attacks')+get_val(st[1]['statistics'],'Dangerous Attacks')

                    if sot>=4 and dang>=28:
                        squadra=home if gh<=ga else away
                        tg(f"🔥 GIOCALO {m}' TiriP:{sot} Dang:{dang}\n{home} {gh}-{ga} {away}\nNEXT GOL: {squadra}")
                        avvisati.add(fid);gol_attesa[fid]=gh+ga
                    time.sleep(1)
                except:continue

            # controllo gol vinti
            for g in live:
                fid=g["fixture"]["id"]
                if fid in gol_attesa:
                    tot=g["goals"]["home"]+g["goals"]["away"]
                    if tot>gol_attesa[fid]:
                        tg(f"✅ GOL VINTO! {g['teams']['home']['name']} {g['goals']['home']}-{g['goals']['away']} {g['teams']['away']['name']}")
                        del gol_attesa[fid]
            time.sleep(180)
        except Exception as e:
            print(f"ERR CACCIA {e}",flush=True);time.sleep(60)

tg("✅ V3 DOPPIO THREAD PARTITO - ORA CERCA PARTITE")
threading.Thread(target=thread_check,daemon=True).start()
threading.Thread(target=thread_caccia,daemon=True).start()

while True:time.sleep(1000)
