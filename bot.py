
import requests
import json

# Configurazione dei parametri
API_KEY = "IL_TUO_API_KEY_QUI"
URL = "https://api-sports.io"

# Parametri per filtrare solo i match in tempo reale (live)
# Puoi anche filtrare per una lega specifica aggiungendo ad esempio: 'league': '39' (Premier League)
params = {
    'live': 'all' 
}

headers = {
    'x-rapidapi-host': 'v3.football.api-sports.io',
    'x-rapidapi-key': API_KEY
}

try:
    # Invio della richiesta GET
    response = requests.get(URL, headers=headers, params=params)
    
    # Verifica se la richiesta è andata a buon fine
    if response.status_code == 200:
        data = response.json()
        
        # Iterazione attraverso i risultati ricevuti
        fixtures = data.get('response', [])
        print(f"Trovate {len(fixtures)} partite in diretta:\n")
        
        for match in fixtures:
            teams = match['teams']
            goals = match['goals']
            status = match['fixture']['status']
            
            home_team = teams['home']['name']
            away_team = teams['away']['name']
            home_goals = goals['home'] if goals['home'] is not None else 0
            away_goals = goals['away'] if goals['away'] is not None else 0
            elapsed_time = status['elapsed']
            
            print(f"[{elapsed_time}'] {home_team} {home_goals} - {away_goals} {away_team}")
            
    else:
        print(f"Errore nella richiesta: Codice {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Si è verificato un errore: {e}")
