import os
import csv
import zipfile
import subprocess
import requests

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEAM = "CLE"

START_YEAR = 2020
END_YEAR = 2025

SPAN = 4
MIN_AB = 20

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

games = []
event_files = []

# --------------------------------------------------
# Download Event Files
# --------------------------------------------------

for year in range(
    START_YEAR,
    END_YEAR + 1
):

    zip_file = os.path.join(
        DATA_DIR,
        f"{year}eve.zip"
    )

    year_dir = os.path.join(
        DATA_DIR,
        str(year)
    )

    if not os.path.exists(zip_file):

        print(f"Downloading {year}...")

        url = (
            f"https://www.retrosheet.org/events/{year}eve.zip"
        )

        r = requests.get(url)

        if r.status_code != 200:

            print(f"Skipping {year}")
            continue

        with open(zip_file, "wb") as f:
            f.write(r.content)

    os.makedirs(
        year_dir,
        exist_ok=True
    )

    with zipfile.ZipFile(
        zip_file,
        "r"
    ) as z:

        z.extractall(year_dir)

    for file in os.listdir(year_dir):

        if file.endswith((".EVA", ".EVN")):

            event_files.append(
                os.path.join(
                    year_dir,
                    file
                )
            )

print(f"\nFound {len(event_files)} event files.")

for sample_file in event_files:

    sample_dir = os.path.dirname(sample_file)

    sample_name = os.path.basename(sample_file)

    year = sample_name[:4]

    result = subprocess.run(
        [
            "cwevent",
            "-y",
            year,
            "-n",
            "-f",
            "0,1,2,3,10,27,28,29,36,37",
            sample_name
        ],
        cwd=sample_dir,
        capture_output=True,
        text=True,
        check=True
    )

    reader = csv.DictReader(
        result.stdout.splitlines()
    )

    current_game = None

    current_home_team = None

    current_away_team = None

    risp_ab = 0

    risp_hits = 0

    for row in reader:

        cleveland_batting = (
    
            (
                row["AWAY_TEAM_ID"] == TEAM
                and
                row["BAT_HOME_ID"] == "0"
            )
    
            or
    
            (
                row["GAME_ID"][:3] == TEAM
                and
                row["BAT_HOME_ID"] == "1"
            )
    
        )
    
        if not cleveland_batting:
            continue
    
        if current_game is None:
    
            current_game = row["GAME_ID"]
    
            current_home_team = current_game[:3]
    
            current_away_team = row["AWAY_TEAM_ID"]
    
        if row["GAME_ID"] != current_game:
    
            game_date = (
                f"{current_game[3:7]}-"
                f"{current_game[7:9]}-"
                f"{current_game[9:11]}"
            )
    
            home_away = (
                "Home"
                if current_home_team == TEAM
                else "Away"
            )
    
            opponent = (
                current_away_team
                if home_away == "Home"
                else current_home_team
            )
    
            games.append(
                {
                    "date": game_date,
                    "game_id": current_game,
                    "opponent": opponent,
                    "home_away": home_away,
                    "hits": risp_hits,
                    "ab": risp_ab
                }
            )
    
            current_game = row["GAME_ID"]
    
            current_home_team = current_game[:3]
    
            current_away_team = row["AWAY_TEAM_ID"]
    
            risp_hits = 0
    
            risp_ab = 0
    
        if (
            row["BASE2_RUN_ID"]
            or
            row["BASE3_RUN_ID"]
        ):
    
            if row["AB_FL"] == "T":
    
                risp_ab += 1
    
                if int(row["H_CD"]) > 0:
    
                    risp_hits += 1

    if current_game is not None:
    
            game_date = (
                f"{current_game[3:7]}-"
                f"{current_game[7:9]}-"
                f"{current_game[9:11]}"
            )
    
            home_away = (
                "Home"
                if current_home_team == TEAM
                else "Away"
            )
    
            opponent = (
                current_away_team
                if home_away == "Home"
                else current_home_team
            )
    
            games.append(
                {
                    "date": game_date,
                    "game_id": current_game,
                    "opponent": opponent,
                    "home_away": home_away,
                    "hits": risp_hits,
                    "ab": risp_ab
                }
            )

games.sort(key=lambda g: g["date"])

results = []

for i in range(len(games) - SPAN + 1):

    span = games[i:i + SPAN]

    total_hits = sum(
        game["hits"]
        for game in span
    )

    total_ab = sum(
        game["ab"]
        for game in span
    )

    if total_ab < MIN_AB:
        continue

    avg = (
        total_hits / total_ab
        if total_ab
        else 0
    )

    results.append(
        {
            "start": span[0]["date"],
            "end": span[-1]["date"],
            "games": span,
            "hits": total_hits,
            "ab": total_ab,
            "avg": avg
        }
    )

results.sort(
    key=lambda r: (
        r["avg"],
        -r["ab"]
    )
)

print(f"Found {len(results)} qualifying spans.\n")

for result in results[:25]:

    print(
        result["start"],
        result["end"],
        result["hits"],
        result["ab"],
        f"{result['avg']:.3f}"
    )
