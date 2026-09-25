def invia_schedina_10():
    fixtures = get_today_fixtures()
    filtrate = []
    analizzate = 0

    for f in fixtures:
        if f["fixture"]["status"]["short"] != "NS": continue
        analizzate += 1
        try:
            mh = get_media_gol_ultime_5(f["teams"]["home"]["id"])
            ma = get_media_gol_ultime_5(f["teams"]["away"]["id"])
            media = (mh + ma) / 2
            if media >= 2.0:
                filtrate.append({
                    "match": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}",
                    "lega": f['league']['name'],
                    "media": round(media,1)
                })
            time.sleep(0.35)
        except: continue

    if not filtrate:
        send(f"🎫 SCHEDINA 10:00: 0 partite con media >=2.0 su {analizzate} di oggi")
        return

    # MESSAGGIO 1: LISTA COMPLETA DI TUTTE LE ODIERNE FILTRATE
    txt1 = f"📋 *TUTTE LE PARTITE ODIERNE FILTRATE*\n*{datetime.now().strftime('%d/%m')}* - Analizzate {analizzate} - Trovate {len(filtrate)} con media >=2.0\n\n"
    for i, p in enumerate(filtrate, 1):
        txt1 += f"{i}. {p['match']} - {p['lega']} (Media {p['media']})\n"
        # Telegram limite 4096 caratteri, spezza se troppa roba
        if len(txt1) > 3500:
            send(txt1)
            txt1 = "📋 *CONTINUA LISTA:*\n\n"
    
    if txt1.strip() != "📋 *CONTINUA LISTA:*\n\n":
        send(txt1)

    # MESSAGGIO 2: SCHEDINA DA 5-6 PIU' FACILI PER QUOTA 1.8
    schedina = filtrate[:6]
    txt2 = f"🎫 *SCHEDINA 10:00 - QUOTA 1.8*\nFiltro: ultime 5 media >=2.0 gol\n\n"
    for i, p in enumerate(schedina, 1):
        txt2 += f"{i}. {p['match']} ({p['media']} gol)\n"
    txt2 += f"\nQuota target 1.8 | Selezionate {len(schedina)} su {len(filtrate)} filtrate"
    send(txt2)
