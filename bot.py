import os,time,requests,threading,json
from flask import Flask
from datetime import datetime,timezone,timedelta
BOT=os.getenv('BOT_TOKEN');CHAT=os.getenv('CHAT_ID');KEY=os.getenv('API_FOOTBALL_KEY')
ITALY=timezone(timedelta(hours=2))
is_paused=False;last_id=0;sot_sent=set();gol_tracker={};gol_fatto=set();av_s_first=set()
TOP={'Italy':135,'England':39,'Spain':140,'Germany':78,'France':61,'Netherlands':88,'Portugal':94,'Belgium':144,'Turkey':203,'Scotland':179,'Austria':218,'Switzerland':207,'Denmark':106,'Sweden':113,'Norway':103,'Poland':107,'Czech Republic':345,'Croatia':210,'Serbia':286,'Greece':197,'Romania':283,'Bulgaria':172,'Hungary':271,'Slovakia':332,'Slovenia':373,'Ireland':344,'Wales':110,'Finland':244,'Iceland':164,'Cyprus':318,'Malta':389,'Luxembourg':261,'Belarus':116}
EU=set(TOP.keys());IDS=set(TOP.values())
def youth(n): return any(k in n.lower() for k in ['u19','u21','women',' w','youth','reserve']) if n else False
def is_top(f):
    try: return f['league']['country'] in EU and f['league']['id'] in IDS and not youth(f['league']['name'])
    except: return False
app=Flask(__name__)
@app.route('/')
def home(): return f'BOT V33.34 LIVE FIX - {datetime.now(ITALY).strftime("%H:%M")}',200
K1=json.dumps({"keyboard":[[{"text":"☰ MENU"}]],"resize_keyboard":True,"is_persistent":True})
K2=json.dumps({"keyboard":[[{"text":"CAMPIONATI"}],[{"text":"CORNER"},{"text":"LIVE @3+"}],[{"text":"DOPPIA"},{"text":"BOLLA 33"}],[{"text":"ESATTI"}],[{"text":"STATUS"},{"text":"TEST LIVE"},{"text":"SPEGNI"},{"text":"ACCENDI"}],[{"text":"⬇️ CHIUDI"}]],"resize_keyboard":True,"is_persistent":True})
def tg(m,cid=None,reply=None):
    try:
        cid=cid or CHAT
        requests.post(f'https://api.telegram.org/bot{BOT}/sendMessage',json={'chat_id':cid,'text':m,'parse_mode':'HTML','reply_markup':json.loads(reply) if isinstance(reply,str) else reply},timeout=25)
    except Exception as e: print(f"TG ERR {e}")
def api(u):
    try:
        r=requests.get(u,headers={'x-apisports-key':KEY},timeout=30)
        if r.status_code==429: print("API LIMIT 429"); return 'LIMIT'
        if r.status_code!=200: print(f"API {r.status_code} {u}"); return []
        return r.json().get('response',[])
    except Exception as e: print(f"API EXC {e}"); return []
def get_sot(fid):
    # PROVA SHOTS ON GOAL + FALLBACK TOTAL SHOTS
    try:
        st=api(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}')
        if not st or st=='LIMIT' or len(st)<2: return 0
        sot=0;total=0
        for s in st:
            for x in s['statistics']:
                if x['type']=='Shots on Goal':
                    try: sot+=int(str(x['value'] or 0))
                    except: pass
                if x['type']=='Total Shots':
                    try: total+=int(str(x['value'] or 0))
                    except: pass
        # SE SOT=0 MA TOTAL ALTO, USA TOTAL/2 come stima
        if sot==0 and total>=4: sot=total//2
        return sot
    except: return 0
def poll():
    global is_paused,last_id,sot_sent,gol_tracker,gol_fatto,av_s_first
    try: requests.get(f'https://api.telegram.org/bot{BOT}/deleteWebhook?drop_pending_updates=true',timeout=10)
    except: pass
    while True:
        try:
            r=requests.get(f'https://api.telegram.org/bot{BOT}/getUpdates?offset={last_id+1}&timeout=20',timeout=35).json()
            if r.get('ok'):
                for u in r.get('result',[]):
                    last_id=u['update_id'];txt=(u.get('message',{}).get('text') or '').strip();cid=u.get('message',{}).get('chat',{}).get('id')
                    if not txt: continue
                    up=txt.upper()
                    if 'MENU' in up and 'CHIUDI' not in up: tg('MENU:',cid,reply=K2);continue
                    if 'CHIUDI' in up: tg('Chiuso - 1 bottone',cid,reply=K1);continue
                    if '/start' in txt.lower(): tg('V33.34 LIVE FIX OK\n- Primo tempo 2+ tiri (era 3)\n- Giocalo 5+ tiri al 70 (era 6)\n- Fallback Total Shots\n- Japan OFF\n- 1 bottone',cid,reply=K1);continue
                    if 'STATUS' in up:
                        games=api('https://v3.football.api-sports.io/fixtures?live=all')
                        live_top=len([g for g in (games if games!='LIMIT' else []) if is_top(g)]) if games and games!='LIMIT' else 0
                        tg(f'STATUS V33.34\nLive totali: {len(games) if games and games!="LIMIT" else 0}\nLive TOP EUROPA: {live_top}\nPT inviati: {len(av_s_first)}\nGIOCALO: {len(sot_sent)}\nGOAL: {len(gol_fatto)}\nSOGLIE: PT 2 tiri / GIOCALO 5 tiri',cid,reply=K1);continue
                    if 'TEST' in up:
                        tg('TEST LIVE - cerco ora...',cid,reply=K1)
                        games=api('https://v3.football.api-sports.io/fixtures?live=all')
                        if not games or games=='LIMIT': tg('TEST: API limite o vuota',cid,reply=K1);continue
                        c=0
                        for g in games[:15]:
                            if not is_top(g): continue
                            fid=g['fixture']['id'];sot=get_sot(fid);m=g['fixture']['status']['elapsed'] or 0
                            h=g['teams']['home']['name'];a=g['teams']['away']['name']
                            tg(f"TEST {h} vs {a} - {m}' - {sot} TIRI - {g['league']['country']}",cid,reply=K1);c+=1;time.sleep(0.8)
                            if c>=5: break
                        if c==0: tg('TEST: Nessun TOP live ora - normale se pausa campionati',cid,reply=K1)
                        continue
                    if 'SPEGNI' in up: is_paused=True;tg('PAUSA',cid,reply=K1);continue
                    if 'ACCENDI' in up: is_paused=False;tg('ATTIVO',cid,reply=K1);continue
        except Exception as e: print(f"POLL {e}")
        time.sleep(1)
def live_loop():
    tg('V33.34 LIVE FIX ATTIVO - Soglie abbassate - Japan OFF - 1 bottone MENU',reply=K1)
    while True:
        try:
            if is_paused: time.sleep(30);continue
            now=datetime.now(ITALY)
            if 0<=now.hour<7: print("Sleep notte"); time.sleep(300);continue
            if now.hour==7 and now.minute<5: sot_sent.clear();gol_tracker.clear();gol_fatto.clear();av_s_first.clear()
            games=api('https://v3.football.api-sports.io/fixtures?live=all')
            if games=='LIMIT': print("LIMIT live, sleep 1h"); time.sleep(3600);continue
            if not games: time.sleep(60);continue
            print(f"LIVE CHECK {len(games)} partite - TOP filter...")
            sent_now=0
            for g in games:
                try:
                    if not is_top(g): continue
                    fid=g['fixture']['id'];m=g['fixture']['status']['elapsed']
                    if m is None: continue
                    if m>90: continue
                    h=g['teams']['home']['name'];a=g['teams']['away']['name'];gh=g['goals']['home'] or 0;ga=g['goals']['away'] or 0;tot=gh+ga
                    sot=get_sot(fid)
                    print(f"{h} vs {a} {m}' {sot} tiri {g['league']['country']}")
                    if sot==0: continue
                    ctry=g['league']['country']
                    # PRIMO TEMPO 2+ TIRI (prima 3) - ABBASSATO!
                    if fid not in av_s_first and m<=50 and sot>=2:
                        tg(f"PRIMO TEMPO {h} {gh}-{ga} {a} - {sot} TIRI al {m}'\n{ctry} - {g['league']['name']}",reply=K1);av_s_first.add(fid);sent_now+=1
                    # GIOCALO 5+ TIRI AL 70 (prima 6) - ABBASSATO!
                    if fid not in sot_sent and m<=75 and sot>=5:
                        tg(f"GIOCALO! {h} {gh}-{ga} {a} - {sot} TIRI al {m}'\n{ctry} - {g['league']['name']}",reply=K1);sot_sent.add(fid);gol_tracker[fid]=tot;sent_now+=1
                    if fid in sot_sent and fid not in gol_fatto and tot>gol_tracker.get(fid,0):
                        tg(f"GOAL! {h} {gh}-{ga} {a} - HA SEGNATO!\n{ctry} - {sot} TIRI al {m}'",reply=K1);gol_fatto.add(fid);sent_now+=1
                    time.sleep(0.4)
                except Exception as e: print(f"LIVE LOOP g {e}"); continue
            print(f"LIVE CYCLE finito - inviati {sent_now}")
            time.sleep(35)
        except Exception as e: print(f"LIVE LOOP ERR {e}"); time.sleep(15)
threading.Thread(target=poll,daemon=True).start()
threading.Thread(target=live_loop,daemon=True).start()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
