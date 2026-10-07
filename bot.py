def lista_under_35():
    try:
        now = datetime.now(ITALY)
        fine_24h = now + timedelta(hours=24)
        OGGI = now.strftime("%Y-%m-%d")
        DOMANI = fine_24h.strftime("%Y-%m-%d")
        fixtures_oggi = api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        fixtures_domani = api_get(f"https://v3.football.api-sports.io/fixtures?date={DOMANI}")
        fixtures = []
        if fixtures_oggi and fixtures_oggi!= "LIMIT": fixtures += fixtures_oggi
        if fixtures_domani and fixtures_domani!= "LIMIT" and DOMANI!= OGGI: fixtures += fixtures_domani
        if not fixtures: return f"Nessuna partita nelle prossime 24H"
        risultati=[]
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt < now: continue
            if dt > fine_24h: continue
            if is_youth(p['league']['name']): continue
            home=p['teams']['home']['name']; away=p['teams']['away']['name']
            paese=p['league']['country']; lega=p['league']['name']; orario=dt.strftime("%d/%m %H:%M")
            qenc=urllib.parse.quote_plus(home+" "+away)
            link_bet365=f"https://www.bet365.it/search?q={qenc}"
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT": continue
            if not odds[0].get("bookmakers"): continue
            for book in odds[0]["bookmakers"]:
                try:
                    for bet in book["bets"]:
                        if "OVER/UNDER" not in bet["name"].upper() and "TOTAL" not in bet["name"].upper(): continue
                        for v in bet["values"]:
                            if "under 4.5" in v["value"].lower():
                                try:
                                    q=float(v["odd"])
                                    # SOTTO 1.15 COME HAI DETTO TU!
                                    if q <= 1.15:
                                        risultati.append(f"🕐 {orario} - {paese} - {lega}\n{home} vs {away}\n👉 UNDER 4.5 @ {q} ({book['name']})\n<a href='{link_bet365}'>BET365</a>")
                                        raise StopIteration
                                except StopIteration:
                                    break
                                except: pass
                except StopIteration:
                    break
                except: continue
            time.sleep(0.12)
        if not risultati: return f"Nessuna Under 4.5 sotto 1.15 nelle prossime 24H"
        return f"⚽ UNDER 4.5 SOTTO 1.15 - PROSSIME 24H ({len(risultati)} partite)\n\n" + "\n\n".join(risultati[:40])
    except Exception as e: return f"Errore under: {e}"
