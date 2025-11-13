import requests
import datetime
import os
import locale

# Asetetaan suomen kieli päivämäärien muotoiluun
try:
    locale.setlocale(locale.LC_TIME, "fi_FI.UTF-8")
except:
    locale.setlocale(locale.LC_TIME, "")

# Joukkueet, joista haluat tulokset
TEAMS = ["ANA", "CAR", "DAL", "MTL"]

def get_team_results():
    url = "https://api-web.nhle.com/v1/schedule/now"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("⚠️ Virhe haettaessa pelidataa:", e)
        return [], []

    results = []
    upcoming = []

    for week in data.get("gameWeek", []):
        for game in week.get("games", []):
            home = game["homeTeam"]["abbrev"]
            away = game["awayTeam"]["abbrev"]

            # Näytä vain valitut joukkueet
            if home not in TEAMS and away not in TEAMS:
                continue

            game_state = game.get("gameState", "UNKNOWN")
            game_time_str = game.get("startTimeUTC")

            if game_time_str:
                game_time = datetime.datetime.fromisoformat(game_time_str.replace("Z", "+00:00"))
                local_time = game_time.astimezone(datetime.timezone(datetime.timedelta(hours=2)))  # Suomen aika
                formatted_time = local_time.strftime("%A %d.%m klo %H:%M")
            else:
                formatted_time = "Aika tuntematon"

            # Erota pelatut ja tulevat pelit
            if game_state in ["FINAL", "OFF"]:
                home_score = game.get("homeTeamScore", 0)
                away_score = game.get("awayTeamScore", 0)
                results.append(f"{away} {away_score} - {home_score} {home} ({game_state})")
            elif game_state in ["FUT", "PRE", "LIVE", "CRIT"]:
                upcoming.append(f"{away} @ {home} — {formatted_time}")

    return results, upcoming


def get_standings():
    url = "https://api-web.nhle.com/v1/standings/now"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("⚠️ Virhe haettaessa sarjataulukkoa:", e)
        return []

    standings = []

    # Jokainen division sisältää joukkueita
    for division in data.get("standings", []):
        for team in division.get("teamRecords", []):
            team_name = team["teamAbbrev"]["default"]
            games_played = team.get("gamesPlayed", 0)
            wins = team.get("wins", 0)
            losses = team.get("losses", 0)
            ot = team.get("otLosses", 0)
            points = team.get("points", 0)
            rank = team.get("leagueSequence", "-")

            standings.append({
                "rank": rank,
                "team": team_name,
                "games": games_played,
                "wins": wins,
                "losses": losses,
                "ot": ot,
                "points": points
            })

    # Järjestetään sijoituksen mukaan
    standings.sort(key=lambda x: x["rank"])
    return standings


def generate_html(results, upcoming, standings):
    today = datetime.date.today().strftime("%d.%m.%Y")
    html_content = f"""
    <html>
    <head>
        <title>NHL {today}</title>
        <meta charset="utf-8"/>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0d1117; color: #e6edf3; }}
            h1, h2 {{ color: #58a6ff; }}
            ul {{ list-style: none; padding-left: 0; }}
            li {{ margin-bottom: 6px; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 800px; margin-top: 10px; }}
            th, td {{ border: 1px solid #30363d; padding: 6px 8px; text-align: center; }}
            th {{ background-color: #161b22; color: #58a6ff; }}
            tr:nth-child(even) {{ background-color: #161b22; }}
        </style>
    </head>
    <body>
        <h1>NHL-tulokset ({today})</h1>
        <ul>
    """

    if results:
        for r in results:
            html_content += f"<li>{r}</li>"
    else:
        html_content += "<li>Ei pelattuja otteluita tänään.</li>"

    html_content += """
        </ul>
        <h2>Tulevat ottelut</h2>
        <ul>
    """

    if upcoming:
        for g in upcoming:
            html_content += f"<li>{g}</li>"
    else:
        html_content += "<li>Ei tulevia otteluita.</li>"

    html_content += """
        </ul>
        <h2>🧾 Sarjataulukko</h2>
        <table>
            <tr>
                <th>Sijoitus</th>
                <th>Joukkue</th>
                <th>Ottelut</th>
                <th>V</th>
                <th>H</th>
                <th>JA</th>
                <th>Pisteet</th>
            </tr>
    """

    if standings:
        for s in standings:
            html_content += f"""
            <tr>
                <td>{s['rank']}</td>
                <td>{s['team']}</td>
                <td>{s['games']}</td>
                <td>{s['wins']}</td>
                <td>{s['losses']}</td>
                <td>{s['ot']}</td>
                <td>{s['points']}</td>
            </tr>
            """
    else:
        html_content += "<tr><td colspan='7'>Ei sarjataulukkoa saatavilla.</td></tr>"

    html_content += f"""
        </table>
        <p>Päivitetty: {datetime.datetime.now().strftime("%H:%M:%S")}</p>
    </body>
    </html>
    """

    output_file = "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ index.html luotu ({output_file})")


if __name__ == "__main__":
    results, upcoming = get_team_results()
    standings = get_standings()
    generate_html(results, upcoming, standings)
    print("🎉 Valmis! Voit nyt puskea tiedoston GitHubiin.")


