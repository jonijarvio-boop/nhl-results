import requests
import datetime
import os

TEAMS = ["ANA", "CAR", "DAL", "MTL", "NSH"]  # lisätty Nashville

# ----------------------- APUFUNKTIOITA -----------------------

def fetch_json(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Virhe haettaessa {url}: {e}")
        return None


def format_game_state(state):
    """Näyttää (kesken) vain LIVE- ja CRIT-tilanteessa."""
    return " (kesken)" if state in ["LIVE", "CRIT"] else ""


def parse_datetime(iso):
    dt = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(datetime.timezone(datetime.timedelta(hours=2)))


def format_finnish_date(dt):
    return dt.strftime("%d.%m.%Y klo %H:%M")


# ----------------------- HAE PELIT -----------------------

def get_schedule():
    url = "https://api-web.nhle.com/v1/schedule/now"
    data = fetch_json(url)
    if not data:
        return []
    games = []
    for week in data.get("gameWeek", []):
        for g in week.get("games", []):
            games.append(g)
    return games


# ----------------------- HAE JOUKKUEKOHTAISET PELIT -----------------------

def get_team_games(team, all_games):
    """Palauttaa (last_game, next_game) joukkueelle."""
    team_games = [g for g in all_games if
                  g.get("homeTeam", {}).get("abbrev") == team or
                  g.get("awayTeam", {}).get("abbrev") == team]

    if not team_games:
        return None, None

    # Järjestä aikajärjestykseen
    team_games_sorted = sorted(team_games, key=lambda g: g.get("startTimeUTC", ""))
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

    last_game = None
    next_game = None

    for g in team_games_sorted:
        start = datetime.datetime.fromisoformat(g.get("startTimeUTC", now.isoformat()).replace("Z", "+00:00"))
        if start < now:
            last_game = g
        else:
            next_game = g
            break

    return last_game, next_game


def format_game_info(game):
    """Muotoilee yhden pelin tiedot nätisti."""
    if not game:
        return "Ei tietoa"

    home = game.get("homeTeam", {}).get("abbrev", "N/A")
    away = game.get("awayTeam", {}).get("abbrev", "N/A")

    hs = game.get("homeTeam", {}).get("score", 0)
    as_ = game.get("awayTeam", {}).get("score", 0)

    state = game.get("gameState", "")
    state_text = format_game_state(state)

    dt = parse_datetime(game.get("startTimeUTC", datetime.datetime.utcnow().isoformat()))
    finnish_time = format_finnish_date(dt)

    return f"{away} {as_} – {hs} {home}{state_text}<br><small>{finnish_time}</small>"


# ----------------------- SARJATAULUKKO -----------------------

def get_standings():
    url = "https://api-web.nhle.com/v1/standings/now"
    data = fetch_json(url)
    if not data:
        return []

    rows = []
    for team in data.get("standings", []):
        abbrev = team.get("teamAbbrev", {}).get("default")
        if abbrev in TEAMS:
            rows.append({
                "team": abbrev,
                "points": team.get("points", 0),
                "wins": team.get("wins", 0),
                "losses": team.get("losses", 0),
                "ot_wins": team.get("otWins", 0),
                "ot_losses": team.get("otLosses", 0)
            })
    return rows


# ----------------------- HTML GENEROINTI -----------------------

def generate_html():
    today = datetime.date.today().strftime("%Y-%m-%d")
    all_games = get_schedule()

    html = f"""
<html>
<head>
    <meta charset="utf-8"/>
    <title>NHL {today}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .team-box {{ border: 2px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 10px; width: 350px; }}
        h2 {{ margin-bottom: 5px; }}
        table {{ border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
    </style>
</head>
<body>

<h1>NHL – joukkueiden viimeisin ja seuraava peli</h1>
"""

    for team in TEAMS:
        last_game, next_game = get_team_games(team, all_games)

        html += f"""
<div class="team-box">
    <h2>{team}</h2>
    <b>Viimeisin peli:</b><br>
    {format_game_info(last_game)}<br><br>
    <b>Seuraava peli:</b><br>
    {format_game_info(next_game)}
</div>
"""

    # Sarjataulukko
    standings = get_standings()
    if standings:
        html += "<h1>Sarjataulukko</h1>"
        html += "<table><tr><th>Joukkue</th><th>Pisteet</th><th>Voitot</th><th>Tappiot</th><th>Jatkoaikavoitot</th><th>Jatkoaikatappiot</th></tr>"
        for row in standings:
            html += f"<tr><td>{row['team']}</td><td>{row['points']}</td><td>{row['wins']}</td><td>{row['losses']}</td><td>{row['ot_wins']}</td><td>{row['ot_losses']}</td></tr>"
        html += "</table>"

    html += f"<p>Päivitetty: {datetime.datetime.now().strftime('%H:%M:%S')}</p></body></html>"

    out_file = "index.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html luotu: {os.path.abspath(out_file)}")


# ----------------------- MAIN -----------------------

if __name__ == "__main__":
    generate_html()
    print("✔ Valmis!")
