def crea_bolla_15():
    try:
        OGGI=datetime.now(ITALY).strftime("%Y-%m-%d")
        fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={OGGI}")
        if not fixtures:
            return f"Nessuna partita oggi {OGGI}"
        picks=[]
        quota_tot=1.0
        BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly","Amateur","Club Friend","College","U18","U17","U16"]
        fixtures=sorted(fixtures,key=lambda x:x["fixture"]["timestamp"])
        for p in fixtures:
            if len(picks)>=20:
                break
            lega=p["league"]["name"]
            if any(b.lower() in lega.lower() for b in BAN):
                continue
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            if dt<datetime.now(ITALY):
                continue
            home=p["teams"]["home"]["name"]
            away=p["teams"]["away"]["name"]
            paese=p["league"]["country"]
            orario=dt.strftime("%H:%M")
            odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"):
                continue
            try:
                over=None
                for bet in odds[0]["bookmakers"][0]["bets"]:
                    if "Over/Under" in bet["name"]:
                        for v in bet["values"]:
                            if "Over 0.5" in v["value"]:
                                q=float(v["odd"])
                                if 1.02 <= q <= 1.20:
                                    over=q
                                    break
                        if over:
                            break
                if not over:
                    continue
                quota_tot=round(quota_tot*over,2)
                picks.append(f"{orario} - {paese} - {lega}\n{home} vs {away}\n-> Over 0.5 @ {over}")
            except:
                continue
        if len(picks)<15:
            return f"Oggi trovate solo {len(picks)} Over 0.5 - quota {quota_tot:.2f}\nRiprova dopo le 12:00 che caricano piu partite"
        return f"BOLLA 20 PARTITE NON 0-0 - Over 0.5 - Quota {quota_tot:.2f}\n\n" + "\n\n".join(picks) + f"\n\nTOT {quota_tot:.2f} - {len(picks)} partite"
    except Exception as e:
        return f"Errore bolla Over: {e}"

# Per compatibilità con tasto ELITE
def crea_bolla_elite():
    return crea_bolla_15()
