
async def live_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Proviamo 2 metodi per beccarle tutte
        data = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        
        if data.get("errors"):
            await update.message.reply_text(f"❌ ERRORE API-SPORTS:\n{data['errors']}\n\nQuesta è la chiave su Render, è sbagliata o bloccata!")
            print(f"API BLOCK: {data['errors']}")
            return

        live = data.get("response", [])
        
        # Se live=all dà 0, proviamo con il secondo metodo
        if len(live) == 0:
            data2 = api_get("https://v3.football.api-sports.io/fixtures?status=1H-HT-2H-ET-P-BT")
            live = data2.get("response", [])
        
        if not live:
            await update.message.reply_text(f"📭 API dice 0 LIVE (results={data.get('results')}).\nMa è strano se sul book ne vedi. Mandami screen dei LOG di Render!")
            return
        
        msg = f"📊 LIVE ORA REALE: {len(live)} partite\n\n"
        for m in live[:20]:
            try:
                fid = m["fixture"]["id"]
                minute = m["fixture"]["status"]["elapsed"] or 0
                home = m["teams"]["home"]["name"][:12]
                away = m["teams"]["away"]["name"][:12]
                score = f"{m['goals']['home'] or 0}-{m['goals']['away'] or 0}"
                shots, corners = get_stats_completo(fid)
                stato = "🔥" if fid in alerted_calda else "⏳"
                msg += f"{stato} {minute}' {home}-{away} {score} T:{shots} C:{corners}\n"
                await asyncio.sleep(0.25)
            except: continue
        
        await update.message.reply_text(msg[:4000])
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")
