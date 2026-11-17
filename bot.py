require('dotenv').config();

const TG_TOKEN = process.env.TG_BOT_TOKEN || process.env.TELEGRAM_BOT_TOKEN || '';
const CHAT_ID = process.env.TG_CHAT_ID || process.env.TELEGRAM_CHAT_ID || '';
const API_KEY = process.env.API_FOOTBALL_KEY || process.env.RAPIDAPI_KEY || process.env.FOOTBALL_API_KEY || '';
const API_HOST = process.env.API_FOOTBALL_HOST || 'v3.football.api-sports.io';
const API_BASE = process.env.API_FOOTBALL_BASE || 'https://v3.football.api-sports.io';
const BASKET_API_HOST = process.env.API_BASKETBALL_HOST || 'v1.basketball.api-sports.io';
const BASKET_API_BASE = process.env.API_BASKETBALL_BASE || 'https://v1.basketball.api-sports.io';

const BET365_LIVE = 'https://www.bet365.com/#/IP/B1';
const BET365_HOME = 'https://www.bet365.com';

function bet365MatchUrl(gameId) {
  if (gameId) return `https://www.bet365.com/#/AC/B1/C1/D8/E${gameId}/F2/`;
  return BET365_LIVE;
}

module.exports = {
  TG_TOKEN, CHAT_ID, API_KEY, API_HOST, API_BASE,
  BASKET_API_HOST, BASKET_API_BASE, BET365_LIVE, BET365_HOME, bet365MatchUrl,
};
