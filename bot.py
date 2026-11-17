// bot.js - Tutto il bot in un unico file. Avvia con: node bot.js
require('dotenv').config();
const axios = require('axios');
const TelegramBot = require('node-telegram-bot-api');

// ============ CONFIG ============
const TG_TOKEN = process.env.TG_BOT_TOKEN || process.env.TELEGRAM_BOT_TOKEN || '';
const CHAT_ID = process.env.TG_CHAT_ID || process.env.TELEGRAM_CHAT_ID || '';
const API_KEY = process.env.API_FOOTBALL_KEY || process.env.RAPIDAPI_KEY || process.env.FOOTBALL_API_KEY || '';
const API_BASE = process.env.API_FOOTBALL_BASE || 'https://v3.football.api-sports.io';
const BASKET_API_BASE = process.env.API_BASKETBALL_BASE || 'https://v1.basketball.api-sports.io';
const BET365_LIVE = 'https://www.bet365.com/#/IP/B1';

function bet365MatchUrl(gameId) {
  if (gameId) return `https://www.bet365.com/#/AC/B1/C1/D8/E${gameId}/F2/`;
  return BET365_LIVE;
}

function todayStr() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const g = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${g}`;
}

// ============ API ============
async function footGet(path, params = {}) {
  if (!API_KEY) throw new Error('API_FOOTBALL_KEY non impostata');
  const res = await axios.get(API_BASE + path, {
    headers: { 'x-apisports-key': API_KEY },
    params, timeout: 20000,
  });
  return res.data;
}

async function basketGet(path, params = {}) {
  if (!API_KEY) throw new Error('API key non impostata');
  const res = await axios.get(BASKET_API_BASE + path, {
    headers: { 'x-apisports-key': API_KEY },
    params, timeout: 20000,
  });
  return res.data;
}

// ============ TELEGRAM ============
let bot = null;

function getBot() {
  if (bot) return bot;
  if (!TG_TOKEN) throw new Error('TG_BOT_TOKEN non impostata');
  bot = new TelegramBot(TG_TOKEN, { polling: true, request: { timeout: 30000 } });
  return bot;
}

function getChatId(override) {
  const id = override || CHAT_ID;
  if (!id) throw new Error('TG_CHAT_ID non impostata');
  return id;
}

async function sendWithBet365(text, gameId, chatId) {
  const b = getBot();
  const cid = getChatId(chatId);
  const url = bet365MatchUrl(gameId);
  return b.sendMessage(cid, text, {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [[{ text: '🎯 VAI SU BET365', url }]],
    },
  });
}

async function sendText(text, chatId) {
  const b = getBot();
  const cid = getChatId(chatId);
  return b.sendMessage(cid, text, { parse_mode: 'HTML' });
}

// ============ TRIPLA LIVE (senza filtri) ============
async function getLiveSoccer() {
  try {
    const data = await footGet('/fixtures', { live: 'all' });
    return Array.isArray(data.response) ? data.response : [];
  } catch (e) {
    console.error('[tripla] errore getLiveSoccer:', e.message);
    return [];
  }
}

function parseScore(g) {
  const home = g?.goals?.home ?? 0;
  const away = g?.goals?.away ?? 0;
  const ht = g?.score?.halftime;
  let sot = 0;
  const st = g?.fixture?.status;
  const elapsed = st?.elapsed ?? 0;
  const short = st?.short ?? '';
  if (short === 'HT') sot = 45;
  else if (typeof elapsed === 'number' && elapsed > 0) sot = elapsed;
  if (ht) {
    const parts = String(ht).split('-');
    if (parts.length === 2) {
      const tot = (parseInt(parts[0], 10) || 0) + (parseInt(parts[1], 10) || 0);
      if (tot > sot) sot = tot;
    }
  }
  return { home, away, sot, short, elapsed };
}

async function check_tripla_automatica() {
  console.log('[tripla] controllo live worldwide...');
  const games = await getLiveSoccer();
  if (!games.length) { console.log('[tripla] nessuna partita live'); return; }

  const arr = games.map((g) => {
    const s = parseScore(g);
    return {
      id: g?.fixture?.id,
      league: g?.league?.name || '',
      country: g?.league?.country || '',
      home: g?.teams?.home?.name || '?',
      away: g?.teams?.away?.name || '?',
      ...s,
    };
  });

  // NO filtro len<=15 e NO filtro sot<3: tutte live, prime 3 per sot
  arr.sort((a, b) => b.sot - a.sot);
  const top = arr.slice(0, 3);

  for (const m of top) {
    const txt =
      `⚽ <b>TRIPLA LIVE</b>\n` +
      `<b>${m.home} - ${m.away}</b>\n` +
      `🏆 ${m.country} · ${m.league}\n` +
      `⏱ Min ${m.sot} (${m.short}) · Risultato ${m.home}-${m.away}`;
    try { await sendWithBet365(txt, m.id); }
    catch (e) { console.error('[tripla] send err:', e.message); }
  }
  console.log(`[tripla] inviate ${top.length} partite`);
}

// ============ BASKET HANDICAP 12+ ============
function extractHandicapValue(label) {
  if (!label) return null;
  const m = String(label).match(/-?\d+(\.\d+)?/);
  return m ? parseFloat(m[0]) : null;
}

function findHandicapOdds(bookmaker) {
  const wanted = ['Spread', 'Handicap', 'Asian Handicap', 'Point Spread'];
  const found = [];
  for (const bm of bookmaker || []) {
    for (const bet of bm.bets || []) {
      if (wanted.includes(bet.name)) {
        for (const v of bet.values || []) {
          const h = extractHandicapValue(v.value);
          if (h !== null && Math.abs(h) >= 12) {
            found.push({ bookmaker: bm.name, market: bet.name, label: v.value, handicap: h, odd: parseFloat(v.odd) || 0 });
          }
        }
      }
    }
  }
  return found;
}

async function run_basket_handicap(cid) {
  const date = todayStr();
  console.log('[basket-handicap] date', date);
  const [gamesRes, oddsRes] = await Promise.allSettled([
    basketGet('/games', { date }),
    basketGet('/odds', { date }),
  ]);
  const games = gamesRes.status === 'fulfilled' ? (gamesRes.value.response || []) : [];
  const odds = oddsRes.status === 'fulfilled' ? (oddsRes.value.response || []) : [];
  console.log(`[basket-handicap] games=${games.length} odds=${odds.length}`);

  const oddsByGame = new Map();
  for (const o of odds) {
    const gid = o?.game?.id;
    if (gid == null) continue;
    const list = oddsByGame.get(gid) || [];
    list.push(o); oddsByGame.set(gid, list);
  }

  const matches = [];
  for (const g of games) {
    const gid = g?.id;
    for (const o of oddsByGame.get(gid) || []) {
      const hs = findHandicapOdds(o.bookmakers);
      if (hs.length) {
        matches.push({ id: gid, league: g?.league?.name || '', country: g?.league?.country || '',
          home: g?.teams?.home?.name || '?', away: g?.teams?.away?.name || '?', date: g?.date, handicaps: hs });
        break;
      }
    }
  }

  console.log(`[basket-handicap] matches con handicap>=12: ${matches.length}`);

  const toSend = matches.slice(0, 20);
  for (const m of toSend) {
    const best = m.handicaps[0];
    const txt = `🏀 <b>HANDICAP 12+</b>\n<b>${m.home} vs ${m.away}</b>\n🏆 ${m.country} · ${m.league}\n📈 ${best.market}: <b>${best.label}</b> @${best.odd} (${best.bookmaker})`;
    try { await sendWithBet365(txt, m.id, cid); } catch (e) { console.error('[basket-handicap] send err:', e.message); }
    await new Promise((r) => setTimeout(r, 1000));
  }
  return matches.length;
}

// ============ BASKET ALERT (10-25 min prima) ============
const alerted = new Set();
let lastDayAlert = '';

async function check_basket_alert() {
  const t = todayStr();
  if (t !== lastDayAlert) { alerted.clear(); lastDayAlert = t; }

  const date = todayStr();
  let games = [];
  try { const data = await basketGet('/games', { date }); games = data.response || []; }
  catch (e) { console.error('[basket-alert] errore:', e.message); return; }

  const now = Date.now();
  const candidates = [];
  for (const g of games) {
    if (!g?.date) continue;
    if (g?.status?.short && ['FT','AOT','AP','POST','CANC','SUSP'].includes(g.status.short)) continue;
    const mins = Math.round((new Date(g.date).getTime() - now) / 60000);
    if (mins >= 10 && mins <= 25) {
      if (alerted.has(g?.id)) continue;
      candidates.push({ g, mins });
    }
  }

  for (const { g, mins } of candidates) {
    const txt = `⏰ <b>BASKET TRA ${mins} MIN</b>\n<b>${g?.teams?.home?.name || '?'} vs ${g?.teams?.away?.name || '?'}</b>\n🏆 ${g?.league?.country || ''} · ${g?.league?.name || ''}`;
    try { await sendWithBet365(txt, g?.id); alerted.add(g?.id); } catch (e) { console.error('[basket-alert] send err:', e.message); }
    await new Promise((r) => setTimeout(r, 1000));
  }
  if (candidates.length) console.log(`[basket-alert] avvisate ${candidates.length} partite`);
}

// ============ DOPPIA + MULTIGOL ODIERNE ============
function findFavorite(oddsEntry) {
  let best = null;
  for (const bm of oddsEntry?.bookmakers || []) {
    for (const bet of bm.bets || []) {
      if (['Match Winner','1X2','Moneyline','To Win Match'].includes(bet.name)) {
        for (const v of bet.values || []) {
          const o = parseFloat(v.odd) || 999;
          if (!best || o < best.odd) best = { odd: o, side: v.value, bookmaker: bm.name };
        }
      }
    }
  }
  return best;
}

async function run_doppia_multigol_odierne() {
  const date = todayStr();
  console.log('[doppia-multigol] date', date);
  let fixtures = [];
  try { const data = await footGet('/fixtures', { date }); fixtures = data.response || []; }
  catch (e) { console.error('[doppia-multigol] fixtures err:', e.message); return 0; }
  console.log(`[doppia-multigol] fixtures oggi: ${fixtures.length}`);

  let oddsResp = [];
  try { const od = await footGet('/odds', { date }); oddsResp = od.response || []; }
  catch (e) { console.error('[doppia-multigol] odds err:', e.message); }

  const oddsByFix = new Map();
  for (const o of oddsResp) {
    const fid = o?.fixture?.id; if (fid == null) continue;
    const list = oddsByFix.get(fid) || []; list.push(o); oddsByFix.set(fid, list);
  }

  let count = 0;
  for (const fx of fixtures) {
    const fid = fx?.fixture?.id;
    let fav = null;
    for (const o of oddsByFix.get(fid) || []) { fav = findFavorite(o); if (fav) break; }
    if (!fav) continue;

    const time = fx?.fixture?.date ? new Date(fx.fixture.date).toLocaleTimeString('it-IT', { hour:'2-digit', minute:'2-digit' }) : '--:--';
    const home = fx?.teams?.home?.name || '?';
    const away = fx?.teams?.away?.name || '?';
    const favTeam = fav.side === 'Home' ? home : fav.side === 'Away' ? away : fav.side;

    const txt = `${time} ${fx?.league?.name || ''}\n<b>${home} vs ${away}</b>\n→ FAV <b>${favTeam}</b> @${fav.odd}\n💡 1X + Multigol 1-5`;
    try { await sendWithBet365(txt, fid); count++; } catch (e) { console.error('[doppia-multigol] send err:', e.message); }
    await new Promise((r) => setTimeout(r, 1000));
    if (count >= 20) break;
  }
  console.log(`[doppia-multigol] inviate ${count} partite`);
  return count;
}

// ============ LIVE LOOP CALCIO WORLDWIDE (gol) ============
const seenGoals = new Map();
let lastDayLoop = '';

async function live_loop_calcio_worldwide() {
  const t = todayStr();
  if (t !== lastDayLoop) { seenGoals.clear(); lastDayLoop = t; }

  let games = [];
  try { const data = await footGet('/fixtures', { live: 'all' }); games = data.response || []; }
  catch (e) { console.error('[live-loop] err:', e.message); return; }

  for (const g of games) {
    const fid = g?.fixture?.id; if (fid == null) continue;
    const s = parseScore(g);
    const key = `${s.home}-${s.away}`;
    const prev = seenGoals.get(fid);
    if (prev && prev !== key) {
      const txt = `⚽ <b>GOL!</b> ${g?.teams?.home?.name || '?'} ${s.home}-${s.away} ${g?.teams?.away?.name || '?'}\n🏆 ${g?.league?.country || ''} · ${g?.league?.name || ''}\n⏱ Min ${s.sot}`;
      try { await sendWithBet365(txt, fid); } catch (e) { console.error('[live-loop] send err:', e.message); }
    }
    seenGoals.set(fid, key);
  }
}

// ============ SCHEDULER ============
function safe(fn, label) {
  return async () => { try { await fn(); } catch (e) { console.error(`[sched:${label}] errore:`, e.message); } };
}

function startScheduler() {
  setInterval(safe(check_tripla_automatica, 'tripla'), 90 * 60 * 1000);
  setInterval(safe(() => run_basket_handicap(), 'basket-handicap'), 3 * 60 * 1000);
  setInterval(safe(check_basket_alert, 'basket-alert'), 5 * 60 * 1000);
  setInterval(safe(run_doppia_multigol_odierne, 'doppia'), 60 * 60 * 1000);
  setInterval(safe(live_loop_calcio_worldwide, 'live-loop'), 60 * 1000);

  setTimeout(safe(check_tripla_automatica, 'tripla'), 10_000);
  setTimeout(safe(() => run_basket_handicap(), 'basket-handicap'), 15_000);
  setTimeout(safe(check_basket_alert, 'basket-alert'), 20_000);
  setTimeout(safe(run_doppia_multigol_odierne, 'doppia'), 25_000);
  setTimeout(safe(live_loop_calcio_worldwide, 'live-loop'), 30_000);
  console.log('[sched] scheduler avviato');
}

// ============ MAIN ============
function main() {
  if (!TG_TOKEN) { console.error('Manca TG_BOT_TOKEN nel .env'); process.exit(1); }
  if (!CHAT_ID) { console.error('Manca TG_CHAT_ID nel .env'); process.exit(1); }
  if (!API_KEY) { console.warn('Attenzione: API_FOOTBALL_KEY non impostata - le chiamate API falliranno'); }

  const bot = getBot();
  const cid = getChatId();

  const keyboard = {
    reply_markup: {
      keyboard: [
        ['⚽ TRIPLA LIVE', '🏀 BASKET HANDICAP 12+'],
        ['⏰ BASKET ALERT', '💡 DOPPIA + MULTIGOL'],
        ['🌍 LIVE CALCIO'],
      ],
      resize_keyboard: true,
    },
  };

  bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, 'Bot attivo. Usa i pulsanti o i comandi:\n/tripla /basket /alert /doppia /live', keyboard);
  });

  bot.onText(/\/tripla|⚽ TRIPLA LIVE/, () => { check_tripla_automatica().catch(e => console.error(e.message)); });
  bot.onText(/\/basket|🏀 BASKET HANDICAP 12\+/, () => { run_basket_handicap().catch(e => console.error(e.message)); });
  bot.onText(/\/alert|⏰ BASKET ALERT/, () => { check_basket_alert().catch(e => console.error(e.message)); });
  bot.onText(/\/doppia|💡 DOPPIA \+ MULTIGOL/, () => { run_doppia_multigol_odierne().catch(e => console.error(e.message)); });
  bot.onText(/\/live|🌍 LIVE CALCIO/, () => { live_loop_calcio_worldwide().catch(e => console.error(e.message)); });

  bot.on('polling_error', (e) => console.error('polling_error:', e.message));

  startScheduler();
  console.log('Bot avviato. Chat ID:', cid);
  sendText('🤖 Bot avviato - scheduler attivo. Comandi: /start /tripla /basket /alert /doppia /live').catch(() => {});
}

main();
