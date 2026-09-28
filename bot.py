        # --- LOGICA GIORNO DOPO LE 07:00 ---
        live = api_get("https://v3.football.api-sports.io/fixtures?live=all")
        if live == "LIMIT": time.sleep(3600); continue

        num_live = len(live)

        # 1. Nessun live dopo le 7 = dorme 3 min
        if num_live == 0:
            print(f"Niente live {now.strftime('%H:%M')} - pausa 3 min", flush=True)
            time.sleep(180)
            continue

        # 2. Decidi quanto spesso aggiornare le stats
        if num_live >= 4:  # BOOM tante partite
            TTL_STATS = 120  # aggiorna stats ogni 2 min
            SLEEP_LOOP = 60  # controlla ogni 60 sec
        else:  # 1-3 partite
            TTL_STATS = 300  # ogni 5 min
            SLEEP_LOOP = 75

        # ... poi nel ciclo stats ...
        d = stats_cache.get(fid)
        if not d or time.time() - d.get('time',0) > TTL_STATS:
            # qui chiama le statistics
