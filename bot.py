import requests, time, threading, os
from datetime import datetime, timedelta, timezone

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_KEY")
_raw = os.environ.get("CHAT_ID","0")
CHAT_IDS = [int(x.strip()) for x in _raw.split(",") if x.strip().lstrip("-").isdigit()]
CHAT_ID = CHAT_IDS[0] if CHAT_IDS else 0

ITALY = timezone(timedelta(hours=2))
pre=[]; av_s=[]; token_usati=0; is_paused=False

def tg(msg,cid=None):
    dests = CHAT_IDS if not cid else [cid]
    for d in dests:
        try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",json={"chat_id":d,"text":msg[:4000]},timeout=10)
        except: pass

def api_get(url):
    global token_usati
    try:
        r=requests.get(url,headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=15).json()
        token_usati+=1
        return r.get("response",[])
    except: return []

def handle(txt,cid):
    t=txt.lower()
    if "token" in t:
        try:
            st=requests.get("https://v3.football.api-sports.io/status",headers={"x-apisports-key":API_FOOTBALL_KEY},timeout=10).json()
            req=st['response']['requests']['current']
            lim=st['response']['requests']['limit_day']
            tg(f"💰 TOKEN VERO: {req}/{lim} rimangono {lim-req}",cid)
        except:
            tg(f"TOKEN locale: {token_usati}",cid)
    elif "blasonate" in t:
        tg("🔥 BLASONATE - Cerco...",cid)
    else:
        tg("Comandi: TOKEN - BLASONATE",cid)

def main():
    offset=0
    print(f"BOT RIPRISTINATO - IDS {CHAT_IDS}")
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",params={"offset":offset,"timeout":30},timeout=35).json()
            for u in r.get("result",[]):
                offset=u["update_id"]+1
                m=u.get("message",{})
                txt=m.get("text","")
                cid=m.get("chat",{}).get("id",CHAT_ID)
                if txt: handle(txt,cid)
        except Exception as e:
            print(e); time.sleep(5)

if __name__=="__main__":
    main()
