def tastiera_eu_completa():
    return {
        "inline_keyboard": [
            [
                {"text": "📋 WEEK LUN-DOM", "callback_data": "lista_week"},
                {"text": "📅 ODIERNA", "callback_data": "lista_oggi"}
            ],
            [
                {"text": "🔑 VEDI TOKEN", "callback_data": "vedi_token"}
            ]
        ]
    }

def vedi_token():
    # ti dice consumo API-Football
    try:
        # se usi api-sports
        resp = api_get("https://v3.football.api-sports.io/status")
        if resp:
            req = resp.get("response", {}).get("requests", {})
            curr = req.get("current", "?")
            limit = req.get("limit_day", "100")
            return f"🔑 TOKEN API\nUsati oggi: {curr}/{limit}\nRimanenti: {int(limit)-int(curr) if str(curr).isdigit() else '?'}"
    except:
        pass
    return "🔑 TOKEN: Controllo non disponibile - controlla su dashboard.api-football.com"

# NEL TUO HANDLER:
# if data == "vedi_token":
#    bot.send_message(chat_id, vedi_token(), parse_mode="HTML", reply_markup=tastiera_eu_completa())
