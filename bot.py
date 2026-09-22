async def live_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        live = get_live()
        if not live:
            await update.message.reply_text("📭 Nessuna partita LIVE ora su API-Sports")
            return
        
        msg = f"📊 LIVE ORA: {len(live)} partite\n\n"
        for m in live[:15]: # prime 15 per non spammare
            try:
                fid = m["fixture"]["id"]
                minute = m["fixture"]["status"]["elapsed"] or 0
                home = m["teams"]["home"]["name"]
                away = m["teams"]["away"]["name"]
                score = f"{m['goals']['home'] or 0}-{m['goals']['away'] or 0}"
                shots, corners = get_stats_completo(fid)
                stato = "🔥CALDA" if fid in alerted_calda else "⏳"
                msg += f"{stato} {minute}' {home}-{away} {score} Tiri:{shots} Corn:{corners}\n"
                await asyncio.sleep(0.3)
            except: continue
        
        msg += f"\n✅ Allarmi già dati: CALDE:{len(alerted_calda)} MORTA:{len(alerted_morta)}"
        await update.message.reply_text(msg[:4000])
    except Exception as e:
        await update.message.reply_text(f"Errore /live: {e}")

# e poi in fondo sostituisci le ultime 5 righe con queste:
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live_debug))
    app.add_error_handler(error_handler)
    app.job_queue.run_repeating(check_all, interval=120, first=10)
    tz = pytz.timezone("Europe/Rome")
    app.job_queue.run_daily(schedina_mattutina, time=time(hour=9, minute=0, tzinfo=tz), name="schedina_9")
    print("Bot DAMI avviato - TUTTO ATTIVO")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False, stop_signals=None)
