
import os, time, threading, requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V41 FINALE STABILE - TUTTO OK", 200

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or ""
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY") or ""
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID") or ""

gia_rossi=set()
gia_calde=set()
partite_seguite={}
schedina_oggi=""

def send(testo):
    try:
        if not TELEGRAM_TOKEN or not CHAT_ID: return
        import telebot
        telebot.TeleBot(TELEGRAM_TOKEN).send_message(CHAT_ID, testo, parse_mode="Markdown")
    except Exception as e: print(f"Send err: {e}")

def check_live():
    while True:
        try:
            if not API_FOOTBALL_KEY:
                print("Manca API_FOOTBALL_KEY!"); time.sleep(60); continue
            headers={"x-apisports-key":API_FOOTBALL_KEY}
            r=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=20)
            lives=r.json().get("response",[])
            print(f"V41 LIVE: {len(lives)}")

            for f in lives:
                fid=f["fixture"]["id"]
                minute=f["fixture"]["status"].get("elapsed") or 0
                if minute==0: continue
                home=f["teams"]["home"]["name"]
                away=f["teams"]["away"]["name"]
                gh=f["goals"]["home"] or 0
                ga=f["goals"]["away"] or 0
                score=f"{home} {gh}-{ga} {away}"

                # Tracking GOL
                if fid in partite_seguite:
                    vecchio=partite_seguite[fid]
                    if f"{gh}-{ga}"!=vecchio["score"]:
                        send(f"⚽ *GOOOL {minute}'!!!*\n{score}\nEra {vecchio['score']} -> {gh}-{ga}")
                        partite_seguite[fid]["score"]=f"{gh}-{ga}"

                # CALDA
                if minute>=30 and gh==0 and ga==0:
                    k=f"calda_{fid}"
                    if k not in gia_calde:
                        try:
                            rs=requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=headers, timeout=15)
                            stats=rs.json().get("response",[])
                            if len(stats)>=2:
                                def getv(td, name):
                                    for s in td.get("statistics",[]):
                                        if name.lower() in s.get("type","").lower():
                                            v=s.get("value")
                                            if v is None: return 0
                                            try: return int(str(v).split('/')[0].strip() or 0)
                                            except: return 0
                                    return 0
                                shots=getv(stats[0],"on goal")+getv(stats[1],"on goal")
                                corners=getv(stats[0],"Corner")+getv(stats[1],"Corner")
                                if shots>=4 or corners>=6:
                                    send(f"🔥 *CALDA {minute}'*\n{score}\nTiri in porta: {shots} Corner: {corners}\n👉 Punta, ti avviso GOL!")
                                    gia_calde.add(k)
                                    partite_seguite[fid]={"score":f"{gh}-{ga}","home":home,"away":away}
                        except: pass

                # ROSSO
                if 5<minute<65 and gh==0 and ga==0:
                    try:
                        rev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=headers, timeout=15)
                        for ev in rev.json().get("response",[]):
                            if ev.get("type")=="Card" and "red" in str(ev.get("detail","")).lower():
                                em=ev.get("time",{}).get("elapsed") or 0
                                if em<70:
                                    k=f"rosso_{fid}_{em}"
                                    if k not in gia_rossi:
                                        send(f"🔴 *ROSSO AL {em}'*\n{score}\nMin {minute}' - ENTRA 0-0 SUBITO!")
                                        gia_rossi.add(k)
                    except: pass

            # Pulisci finite
            live_ids=[x["fixture"]["id"] for x in lives]
            for fid in list(partite_seguite.keys()):
                if fid not in live_ids:
                    del partite_seguite[fid]
            time.sleep(90)
        except Exception as e:
            print(f"Check err: {e}"); time.sleep(90)

def crea_schedina(data_str):
    try:
        headers={"x-apisports-key":API_FOOTBALL_KEY}
        r=requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_str}", headers=headers, timeout=20)
        fixtures=r.json().get("response",[])
        sched=[]
        for f in fixtures:
            if len(sched)>=5: break
            league=f["league"]["name"]
            if any(x in league for x in ["Premier League","Serie A","La Liga","Bundesliga","Ligue 1","Serie B","Champions","Europa"]):
                home=f["teams"]["home"]["name"]
                away=f["teams"]["away"]["name"]
                ora=f["fixture"]["date"][11:16]
                sched.append(f"• {ora} {home} - {away} -> 1X / Over 0.5")
        if sched:
            testo=f"🎫 *SCHEDINA DEL GIORNO {data_str} - Ore 10:00*\nQuota target 1.70 - 4 partite facili\n\n" + "\n".join(sched[:5])
            testo+="\n\n💰 *Quota Tot ~1.67-1.80*\nGioca 2-5€ Dami!"
            send(testo)
        else:
            send(f"🎫 Schedina {data_str}: poche partite oggi, domani meglio!")
    except Exception as e:
        print(f"Schedina err: {e}")

def schedina_job():
    global schedina_oggi
    while True:
        try:
            now=datetime.utcnow()
            # 08:00 UTC = 10:00 Italia
            if now.hour==8 and now.minute<15:
                oggi=datetime.now().strftime("%Y-%m-%d")
                if schedina_oggi!=oggi:
                    crea_schedina(oggi)
                    schedina_oggi=oggi
            time.sleep(60)
        except: time.sleep(60)

def bot_thread():
    import telebot
    while True:
        try:
            if not TELEGRAM_TOKEN:
                print("Manca TELEGRAM_TOKEN"); time.sleep(60); continue
            b=telebot.TeleBot(TELEGRAM_TOKEN)
            b.delete_webhook(drop_pending_updates=True); time.sleep(1)
            @b.message_handler(commands=['start'])
            def s(m): b.reply_to(m, f"✅ V41 LIVE!\nCHAT: {m.chat.id}")
            @b.message_handler(commands=['schedina'])
            def sh(m):
                oggi=datetime.now().strftime("%Y-%m-%d")
                b.reply_to(m, "🎫 Creo schedina...")
                crea_schedina(oggi)
            print("Bot polling startato")
            b.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot err: {e}"); time.sleep(15)

if __name__=="__main__":
    threading.Thread(target=bot_thread, daemon=True).start()
    threading.Thread(target=check_live, daemon=True).start()
    threading.Thread(target=schedina_job, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
