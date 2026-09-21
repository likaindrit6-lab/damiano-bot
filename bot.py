
import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import aiohttp
from datetime import datetime

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
CHAT_ID = os.getenv("CHAT_ID")

API_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY} if API_KEY else {}

gia_inviate = set()

async def get_live(session):
    async with session.get(f"{API_URL}/fixtures?live=all", headers=HEADERS) as r:
        return await r.json()

async def get_stats(session, fixture_id):
    async with session.get(f"{API_URL}/fixtures/statistics?fixture={fixture_id}", headers=HEADERS) as r:
        return await r.json()

def analizza_partita(fixture, stats_data):
    try:
        status = fixture['fixture']['status']['short']
        minute = fixture['fixture']['status']['elapsed'] or 0
        goals_home = fixture['goals']['home'] or 0
        goals_away = fixture['goals']['away'] or 0
        league = fixture['league']['name']
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        fixture_id = fixture['fixture']['id']

        # Filtro minuti che vuoi tu: 45-85
        if minute < 45 or minute > 85:
            return None
        # Filtro risultati che vuoi tu: 0-0, 1-0, 0-1, 1-1
        if (goals_home + goals_away) > 2:
            return None
        if goals_home > 1 and goals_away > 1:
            return None

        if not stats_data.get('response') or len(stats_data['response']) < 2:
            return None

        s_home = {x['type']: x['value'] for x in stats_data['response'][0]['statistics']}
        s_away = {x['type']: x['value'] for x in stats_data['response'][1]['statistics']}

        shots_home = s_home.get('Total Shots') or 0
        shots_away = s_away.get('Total Shots') or 0
        sot_home = s_home.get('Shots on Goal') or 0
        sot_away = s_away.get('Shots on Goal') or 0
        corners = (s_home.get('Corner Kicks') or 0) + (s_away.get('Corner Kicks') or 0)
        dang_home = s_home.get('Dangerous Attacks') or 0
        dang_away = s_away.get('Dangerous Attacks') or 0

        total_shots = (shots_home or 0) + (shots_away or 0)
        total_sot = (sot_home or 0) + (sot_away or 0)
        total_dang = (dang_home or 0) + (dang_away or 0)

        # LOGICA CALDA / MORTA / ROSSO
        segnale = None
        motivo = ""

        #
