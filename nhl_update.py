import requests
import datetime
import locale

# Aseta päivämäärät suomeksi
try:
    locale.setlocale(locale.LC_TIME, "fi_FI.UTF-8")
except:
    # Windowsilla usein toimii tämä vaihtoehto
    locale.setlocale(locale.LC_TIME, "fi_FI")

TEAMS = ["ANA", "CAR", "DAL", "MTL"]

# --- Hakee tulokset ---
def get_team_results():
    url = "https://api-web.nhle.com/v1/schedule/now"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("⚠️ Virhe haettaessa otteludataa:", e)
        return []

    results = []
    game_weeks = data.get("gameWeek", [])
    for week in game_weeks:
        for game in week.get("games", []):
            home = game["homeTeam"]["abbrev"]
            away = game["awayTeam"]["abbrev"]

            if home not in TEAMS and away not in TEAMS:
                continue

            home_score = game.get("homeTeamScore", 0)
            away_score = game.get("awayTeamScore", 0)
            state = game.get("gameState", "Unknown")

            # Muutetaan UTC-aika Suomen aikaan
            game_time = datetime.datetime.fromisoformat(game["startTimeUTC"].replace("Z", "+00:00")) + datetime.timedelta(hours=2)
            formatted_time = game_time.strftime("%A %d.%m.%Y klo %H:%M")

            results.append(f"{away} {away_score} - {home_score} {home} ({state}, {formatted_time})")
    return results


# --- Hakee sarjataulukon ---
def get_standings():
    url = "https://api-web.nhle.com/v1/standings/now"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("⚠️ Virhe haettaessa sarjataulukkoa:", e)
        return []

    standings_html = ""
    divisions = data.get("standings", [])
    added_divisions = set()  # Joukko lisättyjen divisioonien seuraamiseen

    for div in divisions:
        div_name = div["divisionName"]

        # Tarkista, onko divisioona jo lisätty
        if div_name in added_divisions:
            continue

        added_divisions.add(div_name)  # Lisää divisioona joukkoon
        teams = div.get("teamRecords", [])
        standings_html += f"<h3>{div_name}</h3><table border='1' cellspacing='0' cellpadding='4'>"
        standings_html += "<tr><th>Joukkue</th><th>O</th><th>V</th><th>T</th><th>P</th></tr>"
        for t in teams:
            team_name = t["teamAbbrev"]["default"]
            gp = t["gamesPlayed"]
            wins = t["wins"]
            losses = t["losses"]
            points = t["points"]
            standings_html += f"<tr><td>{team_name}</td><td>{gp}</td><td>{wins}</td><td>{losses}</td><td>{points}</td></tr>"
        standings_html += "</table><br>"
    return standings_html


# --- Luo HTML ---
def generate_html(results, standings_html):
    today = datetime.date.today().strftime("%A %d.%m.%Y")
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8"/>
        <title>NHL tulokset ja sarjataulukko</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            h1, h2, h3 {{ color: #003366; }}
            table {{ border-collapse: collapse; margin-bottom: 20px; }}
            th {{ background-color: #003366; color: white; }}
            td, th {{ border: 1px solid #999; padding: 6px 10px; text-align: center; }}
            li {{ margin-bottom: 4px; }}
        </style>
    </head>
    <body>
        <h1>NHL tulokset ja tulevat pelit</h1>
        <h2>{today}</h2>
        <ul>
    """

    if results:
        for r in results:
            html_content += f"<li>{r}</li>"
    else:
        html_content += "<li>Ei otteluita tänään valituille joukkueille.</li>"

    html_content += """
        </ul>
        <hr>
        <h2>Sarjataulukko</h2>
    """ + standings_html + f"""
        <p>Päivitetty: {datetime.datetime.now().strftime("%H:%M:%S")}</p>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ index.html luotu (index.html)")


if __name__ == "__main__":
    results = get_team_results()
    standings_html = get_standings()
    generate_html(results, standings_html)
    print("🎉 Valmis! Voit nyt puskea tiedoston GitHubiin.")

