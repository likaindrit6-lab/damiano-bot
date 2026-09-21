
import os, time, threading, requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V42 CON MORTA - LIVE", 200

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or ""
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY") or ""
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID") or ""

gia_rossi=set()
gia_calde=set()
gia_morte=set()
partite_seguite={}

def send(testo):
    try:
        if not TELEGRAM_TOKEN or not CHAT_ID: return
        import telebot
        telebot.TeleBot(TELEGRAM_TOKEN).send_message(CHAT_ID, testo, parse_mode="Markdown")
    except Exception as e: print(f"Send err: {e}")

def check_live():
    while True:
        try:
            if not API_FOOTBALL_KEY: time.sleep(60); continue
            headers={"x-apisports-key":API_FOOTBALL_KEY}
            r=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=20)
            lives=r.json().get("response",[])
            for f in lives:
                fid=f["fixture"]["id"]
                minute=f["fixture"]["status"].get("elapsed") or 0
                if minute==0: continue
                home=f["teams"]["home"]["name"]
                away=f["teams"]["away"]["name"]
                gh=f["goals"]["home"] or 0
                ga=f["goals"]["away"] or 0
                score=f"{home} {gh}-{ga} {away}"

                # GOL TRACKER
                if fid in partite_seguite:
                    if f"{gh}-{ga}"!=partite_seguite[fid]["score"]:
                        send(f"⚽ *GOOOL {minute}'!!!*\n{score}\nEra {partite_seguite[fid]['score']} -> {gh}-{ga}")
                        partite_seguite[fid]["score"]=f"{gh}-{ga}"

                # STATS
                def get_stats():
                    try:
                        rs=requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=headers, timeout=15)
                        stats=rs.json().get("response",[])
                        if len(stats)<2: return None, None
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
                        return shots, corners
                    except: return None, None

                # CALDA 30'+
                if minute>=30 and minute<70 and gh==0 and ga==0:
                    k=f"calda_{fid}"
                    if k not in gia_calde:
                        shots,corners=get_stats()
                        if shots is not None and (shots>=4 or corners>=6):
                            send(f"🔥 *CALDA {minute}'*\n{score}\nTiri in porta: {shots} Corner: {corners}\n👉 Punta! Ti avviso io se segna!")
                            gia_calde.add(k)
                            partite_seguite[fid]={"score":f"{gh}-{ga}"}

                # MORTA 65'+
                if minute>=65 and gh==0 and ga==0:
                    k=f"morta_{fid}"
                    if k not in gia_morte and k not in gia_calde:
                        shots,corners=get_stats()
                        if shots is not None and shots<=2 and corners<=4:
                            send(f"🥶 *MORTA {minute}' - EVITA!*\n{score}\nTiri in porta: {shots} Corner: {corners}\n❌ Partita bloccata, non puntare!")
                            gia_morte.add(k)

                # ROSSO
                if 5<minute<65 and gh==0 and ga==0:
                    try:
                        rev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=headers, timeout=15)
                        for ev in rev.json().get("response",[]):
                            if ev.get("type")=="Card" and "red" in str(ev.get("detail","")).lower():
                                em=ev.get("time",{}).get("elapsed") or 0
                                kk=f"rosso_{fid}_{em}"
                                if em<70 and kk not in gia_rossi:
                                    send(f"🔴 *ROSSO AL {em}'*\n{score}\nMin {minute}' - ENTRA 0-0 SUBITO!")
                                    gia_rossi.add(kk)
                    except: pass

            time.sleep(90)
        except Exception as e:
            print(f"Err: {e}"); time.sleep(90)

def crea_schedina(data_str):
    try:
        headers={"x-apisports-key":API_FOOTBALL_KEY}
        r=requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_str}", headers=headers, timeout=20)
        fixtures=r.json().get("response",[])
        sched=[]
        for f in fixtures:
            if len(sched)>=5: break
            league=f["league"]["name"]
            if any(x in league for x in ["Premier","Serie A","La Liga","Bundesliga","Ligue 1","Champions"]):
                home=f["teams"]["home"]["name"]; away=f["teams"]["away"]["name"]; ora=f["fixture"]["date"][11:16]
                sched.append(f"• {ora} {home} - {away} -> 1X / Over 0.5")
        if sched:
            send(f"🎫 *SCHEDINA DEL GIORNO {data_str} 10:00*\nQuota 1.70\n\n" + "\n".join(sched[:5]) + "\n\n💰 Quota ~1.70 Gioca 2-5€!")
    except Exception as e: print(e)

def schedina_job():
    inviata=""
    while True:
        try:
            now=datetime.utcnow()
            if now.hour==8 and now.minute<15:
                oggi=datetime.now().strftime("%Y-%m-%d")
                if inviata!=oggi:
                    crea_schedina(oggi); inviata=oggi
            time.sleep(60)
        except: time.sleep(60)

def bot_thread():
    import telebot
    while True:
        try:
            if not TELEGRAM_TOKEN: time.sleep(60); continue
            b=telebot.TeleBot(TELEGRAM_TOKEN)
            b.delete_webhook(drop_pending_updates=True); time.sleep(1)
            @b.message_handler(commands=['start'])
            def s(m): b.reply_to(m, f"✅ V42 CON MORTA LIVE!\nCHAT: {m.chat.id}\nComandi: /schedina")
            @b.message_handler(commands=['schedina'])
            def sh(m):
                b.reply_to(m, "🎫 Creo schedina..."); crea_schedina(datetime.now().strftime("%Y-%m-%d"))
            b.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot err: {e}"); time.sleep(15)

if __name__=="__main__":
    threading.Thread(target=bot_thread, daemon=True).start()
    threading.Thread(target=check_live, daemon=True).start()
    threading.Thread(target=schedina_job, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
