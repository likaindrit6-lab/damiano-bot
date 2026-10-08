def is_blasonata_big(home,away):
    big = [
        "milan","inter","juventus","juve","napoli","roma","lazio","atalanta","fiorentina","bologna","torino",
        "real madrid","barcelona","barca","atletico madrid","sevilla","valencia","villarreal","athletic","betis","sociedad",
        "psg","paris saint","marseille","lyon","lille","monaco","lens",
        "bayern","dortmund","leverkusen","leipzig","stuttgart","frankfurt","werder",
        "manchester city","man city","manchester united","man united","man utd","liverpool","chelsea","arsenal","tottenham","newcastle","brighton","aston villa","west ham",
        "benfica","porto","sporting","ajax","psv","feyenoord","club brugge",
        "flamengo","palmeiras","river plate","boca juniors"
    ]
    t = (home+" "+away).lower()
    for b in big:
        if b in t:
            return True
    return False

def get_lun_dom():
    oggi=datetime.now(ITALY)
    # da OGGI a DOMENICA - come mi dicevi tu, tutta la settimana piena
    weekday=oggi.weekday()
    if weekday == 6: # se oggi e' domenica, prendi da domani
        lun=oggi+timedelta(days=1)
    else:
        lun=oggi # da oggi
    dom=oggi+timedelta(days=(6-weekday)) # domenica di questa settimana
    return lun,dom

def crea_blasonate_lun_sab(): # ora e' LUN-DOM
    try:
        d1,d2=get_lun_dom()
        label=d1.strftime("%d/%m")+"->"+d2.strftime("%d/%m")+" LUN-DOM"
        tutte=[]
        for i in range((d2-d1).days+1):
            giorno=(d1+timedelta(days=i)).strftime("%Y-%m-%d")
            fx=api_get("https://v3.football.api-sports.io/fixtures?date="+giorno)
            if fx=="LIMIT": continue
            # FILTRO 1 - solo leghe top
            fx=[f for f in fx if is_blasonata(f['league']['name'],f['league']['country'])]
            # FILTRO 2 - SOLO BIG - VIA SQUADRE DI MERDA
            fx=[f for f in fx if is_blasonata_big(f['teams']['home']['name'],f['teams']['away']['name'])]
            fx=[f for f in fx if is_team_ok(f['teams']['home']['name'],f['teams']['away']['name'])]
            fx=[f for f in fx if datetime.fromtimestamp(f["fixture"]["timestamp"],tz=ITALY) > datetime.now(ITALY)]
            tutte.extend(fx)
            time.sleep(0.2)

        if not tutte:
            return "🏳️ SOSTA - 0 BLASONATE BIG %s\nNiente Milan, Inter, Real, Barca, City ecc questa settimana" % label

        cand=[]
        for p in sorted(tutte,key=lambda x:x["fixture"]["timestamp"]):
            fid=p["fixture"]["id"]
            dt=datetime.fromtimestamp(p["fixture"]["timestamp"],tz=ITALY)
            home=p['teams']['home']['name']
            away=p['teams']['away']['name']
            paese=p['league']['country']
            lega=p['league']['name']
            flag=get_flag(paese)
            ora=dt.strftime("%d/%m %H:%M")
            odds=api_get("https://v3.football.api-sports.io/odds?fixture="+str(fid))
            if not odds or odds=="LIMIT" or not odds[0].get("bookmakers"): continue
            best=None
            for b in odds[0]["bookmakers"]:
                for bet in b["bets"]:
                    bn=bet["name"].lower()
                    # DOPPIA CHANCE 1X/X2 + MULTIGOL 1-5 come mi dicevi
                    if "double chance" in bn:
                        for v in bet["values"]:
                            ev=v["value"].lower()
                            if "home/away" in ev or ev.strip()=="12": continue
                            try:
                                q=float(v["odd"])
                                if 1.10 <= q <= 1.55:
                                    if not best or q < best["q"]:
                                        best={"q":q,"e":v["value"],"t":"DOPPIA"}
                            except: pass
                    if "multigoal" in bn or "multi goals" in bn:
                        for v in bet["values"]:
                            if "1-5" in v["value"]:
                                try:
                                    q=float(v["odd"])
                                    if 1.10 <= q <= 1.55:
                                        if not best or q < best["q"]:
                                            best={"q":q,"e":v["value"],"t":"MULTIGOL 1-5"}
                                except: pass
            if not best: continue
            qenc=urllib.parse.quote_plus(home+" "+away)
            link="https://www.google.com/search?q="+qenc+"+bet365"
            prob=int((1/best["q"])*100)
            if best["t"]=="DOPPIA":
                tipo="DOPPIA %s" % best["e"].replace("Home/Draw","1X").replace("Draw/Away","X2")
            else:
                tipo="MULTIGOL 1-5 %s" % best["e"]
            txt="%s %s | %s | %s\n%s vs %s\n-> %s @ %s (%s%%)\n%s" % (flag,paese.upper(),ora,lega,home,away,tipo,str(best["q"]),prob,link)
            cand.append({"q":best["q"],"txt":txt})

        if not cand:
            return "0 BLASONATE BIG con quota - %s big trovate ma senza quote ancora" % len(tutte)

        cand=sorted(cand,key=lambda x:x["q"])
        picks=cand[:25]
        tot=1
        for x in picks: tot*=x["q"]
        body="\n\n".join([p["txt"] for p in picks])
        return "🏆 BLASONATE VERE LUN-DOM %s - %s PARTITE BIG - Quota %.2f\nSOLO Milan, Inter, Juve, Real, Barca, PSG, Bayern, City, Chelsea ecc\n\n%s\n\nTOT %.2f - 10€ stellina!" % (label,len(picks),tot,body,tot)
    except Exception as e:
        return "Errore blasonate: "+str(e)
