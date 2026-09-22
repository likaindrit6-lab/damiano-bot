async def check_all(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID or not FOOTBALL_API_KEY:
        return

    for m in get_live():
        fid = m["fixture"]["id"]
        minute = m["fixture"]["status"]["elapsed"] or 0
        home = m["teams"]["home"]["name"]
        away = m["teams"]["away"]["name"]
        score = f"{m['goals']['home'] or 0}-{m['goals']['away'] or 0}"

        shots_on, _ = get_stats(fid)

        # 1. CALDA - 6 tiri in porta
        if shots_on >= 6 and fid not in alerted_calda:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"🔥 CALDA {minute}' {home} vs {away} {score} - {shots_on} tiri in porta - PUNTA"
            )
            alerted_calda.add(fid)
            bet_attive.add(fid)
            last_scores[fid] = score

        # 2. MORTA - fine primo tempo e meno di 3 tiri
        if (minute >= 44 and minute <= 48) and shots_on <= 3 and fid not in alerted_morta and fid not in alerted_calda:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"💀 MORTA HT {home} vs {away} {score} - solo {shots_on} tiri in porta nel 1° tempo"
            )
            alerted_morta.add(fid)

        # 3. GOL - solo se hai puntato (calda)
        if fid in bet_attive:
            old_score = last_scores.get(fid)
            if old_score and old_score!= score:
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚽ GOAL! {home} vs {away} ora {score} - VINTA"
                )
                bet_attive.remove(fid) # tolgo per non avvisare più
            last_scores[fid] = score

        # 4. ROSSO (come prima)
        if fid not in alerted_red and minute <= 60:
            #... qui il tuo codice del rosso che hai già
            pass
