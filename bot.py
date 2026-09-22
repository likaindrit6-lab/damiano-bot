
def schedine_ore_9():
    oggi = date.today().isoformat()
    # Prendi tutte le partite di oggi
    r = requests.get(f"https://v3.football.api-sports.io/fixtures?date={oggi}", headers=HEADERS)
    fixtures_oggi = r.json().get('response', [])
    
    sicure = []
    calde_2gol = []
    
    for f in fixtures_oggi[:20]: # prime 20 per non sforare i 2620 token
        team_id = f['teams']['home']['id']
        # guarda ultime 5 partite di quella squadra
        r2 = requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5", headers=HEADERS)
        last5 = r2.json().get('response', [])
        gol_fatti = 0
        for g in last5:
            # conta gol (da implementare con parsing)
            gol_fatti += 1 # esempio
        
        media = gol_fatti / 5 if last5 else 0
        
        if media >= 2.0:
            calde_2gol.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} - media {media:.1f} gol")
        
        # per la quota 1.7/1.8 prendi quelle con media alta xG
        sicure.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}")

    invia_messaggio(f"📋 SCHEDINA 09:00 QUOTA 1.7/1.8:\n" + "\n".join(sicure[:5]))
    invia_messaggio(f"🔥 SCHEDINA 09:00 MEDIA 2 GOL (ultime 5):\n" + "\n".join(calde_2gol[:5] if calde_2gol else ["Nessuna squadra con media 2 oggi"]))
