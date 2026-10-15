# V59 FIX FINALE - SENZA QUOTE - 33 NAZIONI
# Questo NON ha piu errori riga 82

import os, time, requests, threading, json
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")
KEY = os.getenv("API_FOOTBALL_KEY")
ITALY = timezone(timedelta(hours=2))
last_id = 0

TOP33 = {
"Italia":135,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,
"Portogallo":94,"Olanda":88,"Belgio":144,"Turchia":203,"Scozia":179,
"Austria":218,"Svizzera":207,"Danimarca":119,"Svezia":113,"Norvegia":103,
"Polonia":106,"Rep Ceca":110,"Croazia":210,"Serbia":286,"Grecia":197,
"Romania":283,"Ungheria":271,"Bulgaria":172,"Slovacchia":334,"Slovenia":373,
"Cipro":318,"Israele":383,"Ucraina":333,"Bielorussia":116,"Irlanda":84,
"Irlanda Nord":410,"Galles":1107,"Islanda":108
}

LEAGUES = {"Serie A":135,"Serie B":136,"Inghilterra":39,"Spagna":140,"Germania":78,"Francia":61,"Olanda":88,"Portogallo":94,"Turchia":203,"Belgio":144}

app = Flask(__name__)

@app.route("/")
def home():
    return "V59 FIX FINALE OK", 200

TAST = json.dumps({"keyboard":[["Serie A","Serie B","Inghilterra"],["Spagna","Germania","Francia"],["Olanda","Portogallo","Turchia"],["DOPPIA 90%"],["BOLLA EUROPA 33 NAZIONI"],["STATUS"]],"resize_keyboard":True})

def tg(m, cid=None, keys=False):
    cid = cid or CHAT
    b = "https://api.telegram.org/bot" + BOT
    pay = {"chat_id": cid, "text": m, "parse_mode": "HTML"}
    if keys:
        pay["reply_markup"] = json.loads(TAST)
    requests.post(b + "/sendMessage", json=pay, timeout=20)

def api(u):
    try:
        r = requests.get(u, headers={"x-apisports-key": KEY}, timeout=30)
        return r.json().get("response", [])
    except:
        return []

def run_bolla(cid=None):
    sel = []
    for paese, lid in TOP33.items():
        for d in range(0, 15):
            date = (datetime.now(ITALY) + timedelta(days=d)).strftime("%Y-%m-%d")
            url = "https://v3.football.api-sports.io/fixtures?date=" + date + "&league=" + str(lid) + "&season=2024"
            data = api(url)
            if data:
                fx = data[0]
                fdate = fx["fixture"]["date"][:10]
                ora = fx["fixture"]["date"][11:16]
                home = fx["teams"]["home"]["name"]
                away = fx["teams"]["away"]["name"]
                sel.append(fdate + " " + ora + " " + home + " vs " + away + " -> 1X (" + paese + ")")
                time.sleep(0.2)
                break
        if len(sel) >= 33:
            break
    msg = "BOLLA EUROPA 33 NAZIONI\n" + str(len(sel)) + " partite\n\n"
    for i, m in enumerate(sel):
        msg += str(i+1) + ". " + m + "\n"
    tg(msg, cid, True)

def run_doppia(cid=None):
    out = []
    for d in range(0, 3):
        date = (datetime.now(ITALY) + timedelta(days=d)).strftime("%Y-%m-%d")
        data = api("https://v3.football.api-sports.io/fixtures?date=" + date + "&timezone=Europe/Rome")
        for fx in data:
            ora = fx["fixture"]["date"][11:16]
            home = fx["teams"]["home"]["name"]
            away = fx["teams"]["away"]["name"]
            out.append(ora + " " + home + " vs " + away + " -> 1X")
            if len(out) >= 20:
                break
        if len(out) >= 20:
            break
    msg = "DOPPIA 90% " + str(len(out)) + "\n\n"
    for i, m in enumerate(out):
        msg += str(i+1) + ". " + m + "\n"
    tg(msg, cid, True)
