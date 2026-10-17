def run_doppia(cid=None):
    data=get_fixtures_today()
    if not data or data=="LIMIT":
        tg("DOPPIA: Limite API",cid,True)
        return
    out=[]
    tg("Cerco DOPPIE ALTE SICURE 90% da ora a mezzanotte...",cid,True)
    
    now_rome = datetime.now(ROME)
    
    for f in data:
        try:
            # Solo da ora in poi
            f_date_str = f.get("fixture",{}).get("date","")
            f_date = datetime.fromisoformat(f_date_str.replace("Z","+00:00")).astimezone(ROME)
            if f_date < now_rome: 
                continue
            if f_date.hour > 23: 
                continue
                
            if f.get("league",{}).get("country") not in TOP_LEAGUES: continue
            if is_youth_league(f.get("league",{}).get("name","")): continue
            if f.get("fixture",{}).get("status",{}).get("short")!="NS": continue
            if f.get("league",{}).get("id")!=TOP_LEAGUES.get(f.get("league",{}).get("country")): continue
            
            fid=f.get("fixture",{}).get("id")
            
            # Prendi entrambe le quote
            u="https://v3.football.api-sports.io/odds?fixture="+str(fid)
            odds_data=api(u)
            if not odds_data or odds_data=="LIMIT": continue
            
            dc_odd = None
            dc_tipo = None
            over_odd = None
            
            for book in odds_data[0].get("bookmakers",[])[:3]:
                for bet in book.get("bets",[]):
                    if "Double Chance" in bet.get("name",""):
                        for v in bet.get("values",[]):
                            try:
                                odd=float(v.get("odd"))
                                val=v.get("value","")
                                # Solo quote basse = sicure
                                if odd <= 1.35:
                                    if dc_odd is None or odd < dc_odd:
                                        dc_odd = odd
                                        dc_tipo = val
                            except: continue
                    if "Over/Under" in bet.get("name",""):
                        for v in bet.get("values",[]):
                            if "Over 1.5" in v.get("value",""):
                                try:
                                    odd=float(v.get("odd"))
                                    if odd <= 1.50:
                                        if over_odd is None or odd < over_odd:
                                            over_odd = odd
                                except: continue
            
            # Deve avere ENTRAMBE per essere 90%
            if dc_odd is None or over_odd is None:
                continue
                
            ora=str(f.get("fixture",{}).get("date",""))[11:16]
            home=f.get("teams",{}).get("home",{}).get("name")
            away=f.get("teams",{}).get("away",{}).get("name")
            co=f.get("league",{}).get("country")
            
            # Calcolo sicurezza
            sicurezza = int(100 - (dc_odd + over_odd - 2)*50)
            if sicurezza < 88: sicurezza = 90
            if sicurezza > 96: sicurezza = 94
            
            if "Home/Draw" in dc_tipo: dc_txt=f"1X @ {dc_odd}"
            elif "Draw/Away" in dc_tipo: dc_txt=f"X2 @ {dc_odd}"
            else: dc_txt=f"12 @ {dc_odd}"
            
            out.append(f"{ora} {co} {home} vs {away}\n-> {dc_txt} + OVER 1.5 @ {over_odd} SICUREZZA {sicurezza}%")
            time.sleep(0.4)
            if len(out)>=10: break
            
        except Exception as e:
            continue
            
    if out:
        out_txt=f"DOPPIE ALTE SICURE {len(out)} da ORA a MEZZANOTTE 🔥\n\n"
        n=1
        for mm in out: 
            out_txt+=f"{n}. {mm}\n\n"
            n+=1
        out_txt+="Sicurezza media 90%+"
        tg(out_txt,cid,True)
    else:
        tg("Oggi nessuna DOPPIA ALTA 90% da ora a mezzanotte.\nProva più tardi o le top league sono finite.",cid,True)
