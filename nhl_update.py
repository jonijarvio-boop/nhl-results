import requests
import datetime
import os
import locale

# Ajat suomeksi
try:
    locale.setlocale(locale.LC_TIME, "fi_FI")
except:
    pass

TEAMS = ["ANA", "CAR", "DAL", "MTL", "NSH", "FLA"]


# -------------------- APUFUNKTIOITA --------------------

def to_finnish_time(iso):
    """Muuntaa ISO-ajan suomenkieliseksi, esim: '14.11.2025 klo 02:00'"""
    dt = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()
    return dt.strftime("%d.%m.%Y klo %H:%M")


def fetch_json(url):
    """Yleinen JSON-hakufunktio."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("⚠️ Virhe haettaessa:", url, e)
        return None


# Haetaan pelitiedot

def get_schedule():
    url = "https://api-web.nhle.com/v1/schedule/now"
    data = fetch_json(url)
    if not data:
        return []

    games = []
    for week in data.get("gameWeek", []):
        for game in week.get("games", []):
            games.append(game)
    return games


# Kerää joukkueiden pelit

def get_team_games(team, all_games):
    """Palauttaa (last_game, next_game) joukkueelle."""
    team_games = [g for g in all_games if
                  g["homeTeam"]["abbrev"] == team or g["awayTeam"]["abbrev"] == team]

    if not team_games:
        return None, None

    # Järjestetään aikajärjestykseen
    team_games_sorted = sorted(team_games, key=lambda g: g["startTimeUTC"])

    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

    last_game = None
    next_game = None

    for g in team_games_sorted:
        start = datetime.datetime.fromisoformat(g["startTimeUTC"].replace("Z", "+00:00"))
        if start < now:
            last_game = g
        else:
            next_game = g
            break

    return last_game, next_game


# HTML

def generate_html(all_games):
    today = datetime.date.today().strftime("%Y-%m-%d")

    html = f"""
<html>
<head>
    <meta charset="utf-8"/>
    <title>NHL päivitys {today}</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #111;
            color: #fff;
        }}
        h1 {{
            text-align: center;
        }}
        .team-box {{
            background: #222;
            padding: 15px;
            margin: 15px;
            border-radius: 10px;
        }}
        .game {{
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>

<h1>NHL – Joukkuepäivitykset ({today})</h1>
"""

    # Laattikot joukkueille
    for team in TEAMS:
        last_game, next_game = get_team_games(team, all_games)

        html += f"<div class='team-box'><h2>{team}</h2>"

        # ---- Viimeisin peli ----
        html += "<p><b>Viimeisin peli:</b><br/>"
        if last_game:
            away = last_game["awayTeam"]["abbrev"]
            home = last_game["homeTeam"]["abbrev"]

            home_score = last_game["homeTeam"].get("score", 0)
            away_score = last_game["awayTeam"].get("score", 0)

            state = last_game.get("gameState", "?")

            html += f"{away} {away_score} – {home_score} {home} ({state})<br>"
            html += f"{to_finnish_time(last_game['startTimeUTC'])}"
        else:
            html += "Ei aiempia pelejä"
        html += "</p>"

        # Seuraava peli
        html += "<p><b>Seuraava peli:</b><br/>"
        if next_game:
            away = next_game["awayTeam"]["abbrev"]
            home = next_game["homeTeam"]["abbrev"]

            html += f"{away} @ {home}<br>"
            html += f"{to_finnish_time(next_game['startTimeUTC'])}"
        else:
            html += "Ei tulevia pelejä"
        html += "</p></div>"

    # htmlLopetus
    html += f"""
<p style="text-align:center;">
Päivitetty: {datetime.datetime.now().strftime("%H:%M:%S")}
</p>

</body>
</html>
"""

    filename = "index.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print("index.html luotu:", os.path.abspath(filename))


# -------------------- MAIN --------------------

if __name__ == "__main__":
    games = get_schedule()
    generate_html(games)
    print("✔ Valmis!")
