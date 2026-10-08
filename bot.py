def crea_bolla_elite():
    try:
        picks=[]
        quota_tot=1.0
        oggi=datetime.now(ITALY)
        lunedi=oggi - timedelta(days=oggi.weekday())
        BAN=["U19","U20","U21","U23","Youth","Reserve","Women","Friendly","Club Friend","Amateur"]
        for i in range(7):
            if len(picks)>=15 or quota_tot>=12: break
            data=(lunedi+timedelta(days=i)).strftime("%Y-%m-%d")
            fixtures=api_get(f"https://v3.football.api-sports.io/fixtures?date={data}")
            if not fixtures: continue
            for p in fixtures:
                if len(picks)>=15 or quota_tot>=12: break
                lega=p["league"]["name"]
                if any(b.lower() in lega.lower() for b in BAN): continue
                fid=p["fixture"]["id"]
                dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
                if dt<datetime.now(ITALY): continue
                home=p["teams"]["home"]["name"]; away=p["teams"]["away"]["name"]
                paese=p["league"]["country"]; orario=dt.strftime("%H:%M"); giorno=dt.strftime("%a %d/%m")
                odds=api_get(f"https://v3.football.api-sports.io/odds?fixture={fid}")
                if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
                try:
                    combo=None
                    for bet in odds[0]["bookmakers"][0]["bets"]:
                        name=bet["name"].lower()
                        # CERCA MERCATO UNICO COMBINATO
                        if "double chance" in name and ("goals" in name or "total" in name or "over/under" in name or "multigoal" in name or "combo" in name):
                            for v in bet["values"]:
                                val=v["value"].lower()
                                # MG 1-5 = Under 5.5 / 1-5 gol / Over 0.5
                                if "1-5" in val or "1 - 5" in val or "under 5.5" in val or ("over 0.5" in val and "under 5.5" in val):
                                    q=float(v["odd"])
                                    if 1.25 <= q <= 2.20: # quota unica vera, non superata
                                        combo={"val":v["value"],"q":q}
                                        break
                        # ALTERNATIVA: PlanetWin chiama "1X + MG 1-5"
                        if "multigoal" in name or "multi goal" in name or "1-5" in name:
                            for v in bet["values"]:
                                if "1x" in v["value"].lower() or "x2" in v["value"].lower() or "12" in v["value"].lower():
                                    q=float(v["odd"])
                                    if 1.25 <= q <= 2.20:
                                        combo={"val":v["value"],"q":q}
                                        break
                    if not combo: continue
                    if quota_tot*combo["q"] > 13: continue
                    # pulizia nome
                    dcv=combo["val"].replace("Home/Draw","1X").replace("Draw/Away","X2").replace("Home/Away","12")
                    quota_tot*=combo["q"]
                    quota_tot=round(quota_tot,2)
                    picks.append(f"{giorno} {orario} - {paese} - {lega}\n{home} vs {away}\n-> {dcv} @ {combo['q']}")
                except:
                    continue
        if len(picks)<3:
            return f"Bolla Elite: trovate {len(picks)} con quota unica DC+MG, riprova"
        return f"BOLLA ELITE DC + MG 1-5 [QUOTA UNICA] - Quota {quota_tot:.2f}\n\n" + "\n\n".join(picks) + f"\n\nTOT {quota_tot:.2f}"
    except Exception as e:
        return f"Errore elite: {e}"
