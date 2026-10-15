import os, time, requests, threading, json
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT = os.getenv('BOT_TOKEN')
CHAT = os.getenv('CHAT_ID')
KEY = os.getenv('API_FOOTBALL_KEY')
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

LEAGUES = {'Serie A':135,'Serie B':136,'Inghilterra':39,'Spagna':140,'Germania':78,'Francia':61,'Olanda':88,'Portogallo':94,'Turchia':203,'Belgio':144}

app = Flask(__name__)

@app.route('/')
def home():
    return 'V57 FIX SYNTAX OK', 200

TAST = json.dumps({
    "keyboard":[
        ["Serie A","Serie B","Inghilterra"],
        ["Spagna","Germania","Francia"],
        ["Olanda","Portogallo","Turchia"],
        ["DOPPIA 90%"],
        ["BOLLA EUROPA 33 NAZIONI"],
        ["STATUS"]
    ],
    "resize_keyboard":True
})

def tg(m, cid=None, keys=False):
    try:
        cid = cid or CHAT
        b = 'https://api.telegram.org/bot' + BOT
        pay = {'chat_id': cid, 'text': m, 'parse_mode': 'HTML'}
        if keys:
            pay['reply_markup'] = json.loads(TAST)
        requests.post(b + '/sendMessage', json=pay, timeout=20)
    except:
        pass

def api(u):
    try:
        r = requests.get(u, headers={'x-apisports-key': KEY}, timeout=30)
        return r.json().get('response', [])
    except:
        return []

def get_dc(fid):
    try:
        d = api(f'https://v3.football.api-sports.io/odds?fixture={fid}')
        if not d:
            return "1X @ 1.15"
        for bk in d[0].get('bookmakers', [])[:2]:
            for bet in bk.get('bets', []):
                if 'Double Chance' in bet['name']:
                    best = None
                    odd = 10.0
                    for v in bet['values']:
                        try:
                            o = float(v['odd'])
                            if o < odd:
                                odd = o
                                best = v['value']
                        except:
                            continue
                    if best:
                        if 'Home/Draw' in best:
                            return f"1X @ {odd:.2f}"
                        if 'Draw/Away' in best:
                            return f"X2 @ {odd:.2f}"
                        if '
