
import os, asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
import aiohttp
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
API = os.getenv("API_FOOTBALL_KEY")
CHAT = os.getenv("CHAT_ID")

gia_inviate = set()

async def get_live(session):
    async with session.get("https://v3.football.api-sports.io/fixtures?live=all", headers={"x-apisports-key": API}) as r:
        return await r.json()

async def get_stats(session, fid):
    async with session.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers={"x-apisports-key": API}) as r:
        return await r.json()

def analizza(fixture, stats_data):
    try:
        minute = fixture['fixture']['status']['elapsed'] or 0
        gh = fixture['goals']['home'] or 0
        ga = fixture['goals']['away'] or 0
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        league = fixture['league']['name']
        fid = fixture['fixture']['id']

        if minute < 45 or minute > 85: return None
        if gh + ga > 2: return None

        if not stats_data.get('response') or len(stats_data['response']) < 2: return None

        sh = {x['type']: x['value'] for x in stats_data['response'][0]['statistics']}
        sa
