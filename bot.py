
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
    except:
        pass
    return False

def segna_inviato(text):
    try:
        with open(INVIATI_FILE, "a") as f:
            f.write(text + "\n---\n")
    except:
        pass

def send(text):
    if gia_inviato(text):
        print(f"Blocco duplicato, non invio: {text[:50]}")
        return False
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=15)
        print(f"Telegram risponde: {r.status_code} - {r.text[:100]}")
        if r.status_code == 200:
            segna_inviato(text)
            print(f"INVIATO OK: {text[:80]}")
            return True
    except Exception as e:
        print(f"Errore invio: {e}")
    return False

# Manda UN SOLO messaggio quando parte, poi mai più spam
send(f"✅ BOT SISTEMATO {datetime.now().strftime('%H:%M')} - Ora gira 1 volta sola, senza spam. Puoi andare a lavorare tranquillo.")

print("Bot partito e stabile, vivo...")

while True:
    try:
        # --- QUI SOTTO RIMETTIAMO LA TUA LOGICA DELLE 10:30 ---
        # Quando mi dirai la regola, la aggiungo io qui.
        # Per ora resta in attesa senza spammare.
        
        print(f"Controllo {datetime.now().strftime('%H:%M:%S')} - tutto ok, in attesa")
        time.sleep(60)
        
    except Exception as e:
        print(f"Errore nel loop: {e}")
        time.sleep(60)
