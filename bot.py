
import os, time, threading, requests
from flask import Flask
from datetime import datetime
import pytz

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V40 - SCHEDINA 1.70 QUOTA VERA", 200

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")

gia_rossi=set()
gia_calde=set()
gia_morte=set()
partite_seguite={}
schedina_oggi=""

def send(testo):
    try:
        import telebot
        telebot.TeleBot(TELEGRAM_TOKEN).send_message(CHAT_ID, testo, parse_mode="Markdown")
    except Exception as e: print(e)

def check():
    while True:
        try:
            headers={"x-apisports-key":API_FOOTBALL_KEY}
            r=requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=15)
            lives=r.json().get("response",[])
            print(f"V40: {len(lives)} LIVE")

            for f in lives:
                fid=f["fixture"]["id"]
                minute=f["fixture"]["status"].get("elapsed") or 0
                home=f["teams"]["home"]["name"]
                away=f["teams"]["away"]["name"]
                gh=f["goals"]["home"] or 0
                ga=f["goals"]["away"] or 0
                score=f"{home} {gh}-{ga} {away}"

                # STATS
                shots_on=corners=dangerous=total=0
                try:
                    rs=requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=headers, timeout=10)
                    data=rs.json().get("response",[])
                    if len(data)>=2:
                        def get(td,name):
                            for s in td.get("statistics",[]):
                                if name.lower() in s.get("type","").lower():
                                    v=s.get("value")
                                    if v is None: return 0
                                    if isinstance(v,int): return v
                                    try: return int(str(v).split('/')[0])
                                    except: return 0
                            return 0
                        shots_on=get(data[0],"on goal")+get(data[1],"on goal")
                        corners=get(data[0],"Corner")+get(data[1],"Corner")
                        dangerous=get(data[0],"Dangerous")+get(data[1],"Dangerous")
                        total=get(data[0],"Total Shots")+get(data[1],"Total Shots")
                except: pass

                # ROSSO
                if gh==0 and ga==0 and 5<minute<60:
                    try:
                        rev=requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fid}", headers=headers, timeout=10)
                        for ev in rev.json().get("response",[]):
                            if ev.get("type")=="Card" and "red" in str(ev.get("detail","")).lower():
                                em=ev.get("time",{}).get("elapsed") or 0
                                if em<60:
                                    k=f"rosso_{fid}_{em}"
                                    if k not in gia_rossi:
                                        send(f"🔴 *ROSSO AL {em}'*\n{score}\nMin {minute}' - ENTRA 0-0!")
                                        gia_rossi.add(k)
                                        partite_seguite[fid]={"score":f"{gh}-{ga}","corners":corners,"home":home,"away":away}
                    except: pass

                # CALDA + TRACKING GOL
                if minute>=30 and ((gh==0 and ga==0) or (gh==1 and ga==0) or (gh==0 and ga==1)):
                    if shots_on>=5 or (dangerous>=40 and total>=10) or corners>=7:
                        k=f"calda_{fid}_{minute//10}"
                        if k not in gia_calde:
                            send(f"🔥 *CALDA {minute}'*\n{score}\nTiri in porta:{shots_on} Peric:{dangerous} Corner:{corners}\n👉 PUNTA! Io ti dico quando segna!")
                            gia_calde.add(k)
                            partite_seguite[fid]={"score":f"{gh}-{ga}","corners":corners,"home":home,"away":away}

                if fid in partite_seguite:
                    vecchio=partite_seguite[fid]
                    if f"{gh}-{ga}"!=vecchio["score"]:
                        send(f"⚽ *GOOOL {minute}'!!!*\n{score}\nEra {vecchio['score']} ora {gh}-{ga}!")
                        partite_seguite[fid]["score"]=f"{gh}-{ga}"
                    if corners>=vecchio["corners"]+2:
                        send(f"🚩 *Corner {minute}'* {score} -> Corner {corners}")
                        partite_seguite[fid]["corners"]=corners

            # Pulisci finite
            live_ids=[x["fixture"]["id"] for x in lives]
            for fid in list(partite_seguite.keys()):
                if fid not in live_ids:
                    send(f"🏁 Finita: {partite_seguite[fid]['home']} {partite_seguite[fid]['score']} {partite_seguite[fid]['away']}")
                    del partite_seguite[fid]

            time.sleep(90)
        except Exception as e:
            print(e); time.sleep(90)

def schedina_job():
    global schedina_oggi
    while True:
        try:
            italy=pytz.timezone('Europe/Rome')
            now=datetime.now(italy)
            # Per test la manda anche se scrivi /schedina, ma automatico alle 10:00
            if now.hour==10 and now.minute<10:
                oggi=now.strftime("%Y-%m-%d")
                if schedina_oggi!=oggi:
                    crea_schedina(oggi)
                    schedina_oggi=oggi
            time.sleep(60)
        except Exception as e:
            print(f"Err schedina job: {e}"); time.sleep(60)

def crea_schedina(data_str):
    try:
        print(f"Creo schedina {data_str}")
        headers={"x-apisports-key":API_FOOTBALL_KEY}
        # 1. Prendi partite di oggi
        r=requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_str}", headers=headers, timeout=15)
        fixtures=r.json().get("response",[])

        schedina=[]
        quota_tot=1.0

        for f in fixtures:
            if len(schedina)>=5: break
            fid=f["fixture"]["id"]
            league=f["league"]["name"]
            # Solo campionati seri
            if not any(x in league for x in ["Premier","Serie A","LaLiga","La Liga","Bundesliga","Ligue 1","Eredivisie","Primeira","Super Lig","Champions","Europa"]):
                continue

            home=f["teams"]["home"]["name"]
            away=f["teams"]["away"]["name"]
            ora=f["fixture"]["date"][11:16]

            # 2. Prendi quote vere
            try:
                ro=requests.get(f"https://v3.football.api-sports.io/odds?fixture={fid}&bookmaker=8", headers=headers, timeout=15)
                odds_data=ro.json().get("response",[])
                if not odds_data: continue
                bets=odds_data[0].get("bookmakers",[])[0].get("bets",[])

                # Cerca quota bassa 1X o Over 0.5
                for bet in bets:
                    if bet["name"]=="Double Chance":
                        for val in bet["values"]:
                            # 1X a quota 1.15-1.30 è perfetto
                            q=float(val["odd"])
                            if val["value"]=="Home/Draw" and 1.10 <= q <= 1.30:
                                schedina.append(f"• {home} - {away} ({ora}) -> 1X @ {q}")
                                quota_tot*=q
                                raise StopIteration
                    if bet["name"]=="Goals Over/Under" and len(schedina)<5:
                        for val in bet["values"]:
                            if "Over 0.5" in val["value"]:
                                q=float(val["odd"])
                                if 1.05 <= q <= 1.20:
                                    schedina.append(f"• {home} - {away} ({ora}) -> Over 0.5 @ {q}")
                                    quota_tot*=q
                                    raise StopIteration
            except StopIteration:
                continue
            except Exception as e:
                print(f"Err odds {fid}: {e}")
                continue

        if len(schedina)>=4:
            testo=f"🎫 *SCHEDINA DEL GIORNO {data_str} ore 10:00*\nQuota Obiettivo 1.70\n\n" + "\n".join(schedina[:5])
            testo+=f"\n\n💰 *Quota Totale: {quota_tot:.2f}*\n🎯 4/5 partite facili, quota bassa sicura!\nGioca 2-5€ Dami!"
            send(testo)
        else:
            # Fallback se API quote finite, fa schedina senza quota ma sicura
            fallback=[]
            for f in fixtures[:5]:
                home=f["teams"]["home"]["name"]
                away=f["teams"]["away"]["name"]
                ora=f["fixture"]["date"][11:16]
                fallback.append(f"• {home} - {away} ({ora}) -> 1X / Over 0.5")
            testo=f"🎫 *SCHEDINA DEL GIORNO {data_str}*\n\n" + "\n".join(fallback)
            testo+=f"\n\n💰 Quota stimata ~1.70\nOggi quote API finite, ma partite facili!"
            send(testo)

    except Exception as e:
        print(f"Err crea schedina: {e}")
        send(f"🎫 Schedina {data_str}: errore, ma gioca Over 0.5 sulle big di oggi!")

def bot_thread():
    import telebot
    while True:
        try:
            b=telebot.TeleBot(TELEGRAM_TOKEN)
            b.delete_webhook(drop_pending_updates=True); time.sleep(2)
            @b.message_handler(commands=['start'])
            def s(m): b.reply_to(m, f"V40 ATTIVO!\nSchedina 1.70 alle 10:00 + Gol + Calde\nCHAT: {m.chat.id}")
            @b.message_handler(commands=['schedina'])
            def sched(m):
                oggi=datetime.now(pytz.timezone('Europe/Rome')).strftime("%Y-%m-%d")
                b.reply_to(m, "Creo schedina ora...")
                crea_schedina(oggi)
            b.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(e); time.sleep(10)

if __name__=="__main__":
    threading.Thread(target=bot_thread, daemon=True).start()
    threading.Thread(target=check, daemon=True).start()
    threading.Thread(target=schedina_job, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
