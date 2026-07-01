import os
import zipfile
import requests
from collections import defaultdict

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

event_files = []

# Download 2021-2025 Retrosheet event files
for year in range(2021, 2026):

    zip_file = os.path.join(DATA_DIR, f"{year}eve.zip")
    year_dir = os.path.join(DATA_DIR, str(year))

    if not os.path.exists(zip_file):

        print(f"Downloading {year}...")

        url = f"https://www.retrosheet.org/events/{year}eve.zip"

        r = requests.get(url)

        if r.status_code != 200:
            print(f"Skipping {year}")
            continue

        with open(zip_file, "wb") as f:
            f.write(r.content)

    os.makedirs(year_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file, "r") as z:
        z.extractall(year_dir)

    for file in os.listdir(year_dir):

        if file.endswith(".EVA") or file.endswith(".EVN"):

            event_files.append(
                os.path.join(year_dir, file)
            )

print(f"Found {len(event_files)} event files\n")

games = {}

for event_file in event_files:

    current_game = None
    current_date = None
    visteam = None
    hometeam = None

    with open(event_file, encoding="latin-1") as f:

        for raw_line in f:

            line = raw_line.strip()

            if line.startswith("id,"):

                current_game = line.split(",")[1]

                games[current_game] = {
                    "date": "",
                    "opponent": "",
                    "home_away": "",
                    "wp_runs": 0,
                    "plays": []
                }

                continue

            if line.startswith("info,date,"):

                current_date = line.split(",")[2]
                games[current_game]["date"] = current_date
                continue

            if line.startswith("info,visteam,"):

                visteam = line.split(",")[2]
                continue

            if line.startswith("info,hometeam,"):

                hometeam = line.split(",")[2]

                # Determine if Cleveland is home or away
                if hometeam == "CLE":
                    games[current_game]["home_away"] = "Home"
                    games[current_game]["opponent"] = visteam
                elif visteam == "CLE":
                    games[current_game]["home_away"] = "Away"
                    games[current_game]["opponent"] = hometeam

                continue

            if not line.startswith("play,"):
                continue

            fields = line.split(",")

            inning = fields[1]
            batting_team = fields[2]
            batter_id = fields[3]
            event = fields[6]

            team_abbr = visteam if batting_team == "0" else hometeam

            # Only Cleveland batting
            if team_abbr != "CLE":
                continue

            # Must be a wild pitch that scores at least one run
            if "WP" not in event:
                continue

            if "-H" not in event:
                continue

            runs = event.count("-H")

            games[current_game]["wp_runs"] += runs

            games[current_game]["plays"].append({
                "inning": inning,
                "event": event,
                "runs": runs
            })

print("\nGames with 2+ Wild Pitch Runs\n")

for game in sorted(
    games.values(),
    key=lambda x: x["date"]
):

    if game["wp_runs"] < 2:
        continue

    print(
        f"{game['date']} | "
        f"{game['opponent']} | "
        f"{game['home_away']} | "
        f"{game['wp_runs']} runs"
    )

    for play in game["plays"]:

        print(
            f"   Inning {play['inning']} | "
            f"{play['runs']} run(s) | "
            f"{play['event']}"
        )

    print()
