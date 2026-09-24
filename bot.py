import os, requests, time
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

INVIATI_FILE = "/tmp/inviati.txt"

def gia_inviato(text):
    try:
        if os.path.exists(INVIATI_FILE):
            with open(INVIATI_FILE, "r") as f:
                return text in f.read()
    except: pass
    return False

def segna_inviato(text):
    try:
        with open(INVIATI_FILE, "a") as f:
            f.write(text + "\n---\n")
    except: pass

def send(text):
    if gia_inviato(text):
        print(f"Blocco duplicato: {text[:50]}")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=15)
        segna_inviato(text)
        print(f"INVIATO: {text[:80]}")
    except Exception as e:
        print(f"Errore: {e}")

# NON mandiamo più "Bot riavviato" ad ogni deploy, così non fa mai doppio
print("Bot partito, vivo e in attesa...")

while True:
    try:
        # QUI sotto ci rimettiamo la logica Gol / schedine delle 10:30
        # Es: if condizione -> send("🥅 Goianésia vs Rio Verde - Gol")
        
        time.sleep(60)
    except Exception as e:
        print(f"Errore loop: {e}")
        time.sleep(60)
