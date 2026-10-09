import os,time,requests,threading,json,urllib.parse
from flask import Flask
from datetime import datetime,timezone,timedelta

# --- 1. CONFIGURAZIONE - PRENDE I DATI DA RENDER ---
BOT_TOKEN=os.getenv("BOT_TOKEN") # Token del bot Telegram che hai messo su Render
CHAT_ID=os.getenv("CHAT_ID") # Il tuo ID Telegram dove manda i messaggi
API_FOOTBALL_KEY=os.getenv("API_FOOTBALL_KEY") # Chiave per API-Football (risultati live)
ITALY=timezone(timedelta(hours=2)) # Fuso orario Italia, serve per orario partite

# --- 2. MEMORIA DEL BOT - QUI RICORDA COSA HA GIA' SEGNALATO ---
is_paused=False # Se True il bot e' in pausa e non manda segnali
last_update_id=0 # Ultimo messaggio letto su Telegram, per non rileggere sempre
av_g={} # Dizionario: partita_id -> numero gol quando l'ha segnalata (per capire se ha segnato dopo)
av_s=set() # Set di partite gia' segnalate come GIOCALO, cosi non le rispamma
pre=set() # Partite gia' segnalate come PREPARATI
pre1=set() # Partite gia' segnalate come FINE 1T
cache={} # Cache dei tiri in porta, cosi non chiama API ogni secondo
tripla_coda=[] # Lista di partite buone da mettere nella tripla oraria
ultimo_invio_tripla=time.time() # Quando ha mandato l'ultima tripla

# --- 3. LISTA CAMPIONATI EUROPEI CHE VUOI MONITORARE ---
# Ogni numero e' l'ID della lega su API-Football
LEAGUES = {
    "Serie A": 135, "Serie B": 136, "Serie C": 138,
    "Inghilterra": 39, "Championship": 40,
    "Spagna": 140, "Olanda": 88,
