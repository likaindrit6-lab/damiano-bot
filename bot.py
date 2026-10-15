import os, time, requests, threading, json
from flask import Flask
from datetime import datetime, timezone, timedelta

BOT = os.getenv('BOT_TOKEN')
CHAT = os.getenv('CHAT_ID')
KEY = os.getenv('API_FOOTBALL_KEY')

ITALY = timezone(timedelta(hours=2))
is_paused = False
last_id = 0
last_bolla_hour = -1

LEAGUES = {
    'Serie A': 135,
    'Serie B': 136,
    'Inghilterra': 39,
    'Spagna': 140,
    'Germania': 78,
    'Francia': 61,
    'Olanda': 88,
    'Portogallo': 94,
    'Turchia': 203,
    'Belgio': 144
}

TOP = {
    'Italy': 135,
    'England': 39,
    'Spain': 140,
    'Germany': 78,
    'France': 61,
    'Netherlands': 88,
    'Portugal': 94,
    'Belgium': 144,
    'Turkey': 203,
    'Scotland': 179,
    'Austria': 218,
    'Switzerland': 207,
    'Denmark': 106,
    'Sweden':
