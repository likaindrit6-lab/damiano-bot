
# V42 FINALE - Dami - ROSSO 0-0 / CALDA 5 tiri in porta / MORTA 3 tiri totali
import time
import requests

API_KEY = "INSERISCI_QUI_LA_TUA_API_KEY"
BOT_TOKEN = "INSERISCI_QUI_TOKEN_TELEGRAM"
CHAT_ID = "INSERISCI_QUI_CHAT_ID"

HEADERS = {"x-apisports-key": API_KEY}
partite_calde = {}

def manda(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}"
    requests.get(url)
    print(msg)

while True:
    try:
        live = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS).json()
        for f in live['response']:
            casa = f['teams']['home']['name']
            ospite = f['teams']['away']['name']
            minuti = f['fixture']['status']['elapsed'] or 0
            risultato = f"{f['goals']['home']}-{f['goals']['away']}"
            fid = f['fixture']['id']
            if minuti == 0: continue

            s = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEADERS).json()
            try:
                tp = int(s['response'][0]['statistics'][4]['value'] or 0) + int(s['response'][1]['statistics'][4]['value'] or 0)
                tt = int(s['response'][0]['statistics'][2]['value'] or 0) + int(s['response'][1]['statistics'][2]['value'] or 0)
                rc = int(s['response'][0]['statistics'][10]['value'] or 0) + int(s['response'][1]['statistics'][10]['value'] or 0)
            except: continue

            # 🔴 ROSSO 0-0 ENTRO 70°
            if rc > 0 and minuti <= 70 and risultato == "0-0":
                manda(f"🔴 ROSSO 0-0 al {minuti}'\n{casa} vs {ospite}")

            # 🔥 CALDA 5 tiri in porta TOTALI entro 60'
            if tp >= 5 and minuti <= 60 and fid not in partite_calde:
                partite_calde[fid] = f"CALDA al {minuti}'
