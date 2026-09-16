import requests
from bs4 import BeautifulSoup
import time

TOKEN = "INSERISCI_QUI_IL_TOKEN_DEL_TUO_BOT"
URL = f"https://api.telegram.org/bot{TOKEN}/"

def get_updates(offset=0):
    try:
        r = requests.get(URL + "getUpdates", params={"offset": offset, "timeout": 60}, timeout=70)
        return r.json()
    except:
        return {"result": []}

print("Bot avviato!")
offset = 0
while True:
    data = get_updates(offset)
    for update in data.get("result", []):
        offset = update["update_id"] + 1
        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")
            # Risponde a qualsiasi messaggio
            requests.get(URL + "sendMessage", params={"chat_id": chat_id, "text": f"Ricevuto: {text}"})
    time.sleep(1)
