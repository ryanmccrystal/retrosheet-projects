import os
import csv
import zipfile
import subprocess
import requests

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEAM = "NYN"

START_YEAR = 1986
END_YEAR = 1986

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

event_files = []

game_assists = {}

game_info = {}

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

    for filename in os.listdir(year_dir):

        if filename.endswith((".EVA", ".EVN")):

            event_files.append(
                os.path.join(
                    year_dir,
                    filename
                )
            )

print(
    f"\nFound {len(event_files)} event files."
)

# --------------------------------------------------
# Process Event Files
# --------------------------------------------------

for event_file in event_files:

    sample_dir = os.path.dirname(event_file)

    sample_name = os.path.basename(event_file)

    print(
        f"Processing {sample_name}"
    )

    result = subprocess.run(
        [
            "cwevent",
            "-y",
            str(START_YEAR),
            "-n",
            "-f",
            "0,1,2,3,23,24,25,29,91,92,93,94,95",
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

    for row in reader:

        # ------------------------------------------
        # Determine batting team
        # ------------------------------------------

        if row["BAT_HOME_ID"] == "1":

            batting_team = row["GAME_ID"][0:3]

        else:

            batting_team = row["AWAY_TEAM_ID"]

        if batting_team != TEAM:
            continue

        game_id = row["GAME_ID"]

        # ------------------------------------------
        # Determine opponent and home/away
        # ------------------------------------------

        home_team = game_id[0:3]

        away_team = row["AWAY_TEAM_ID"]

        if home_team == TEAM:

            opponent = away_team
            home_away = "Home"

        else:

            opponent = home_team
            home_away = "Away"

        # Save game information
        game_info[game_id] = {
            "opponent": opponent,
            "home_away": home_away
        }

        # ------------------------------------------
        # Create game entry
        # ------------------------------------------

        if game_id not in game_assists:

            game_assists[game_id] = {}

        # ------------------------------------------
        # Examine all assist fields
        # ------------------------------------------

        for assist_field in [
            "ASS1_FLD_CD",
            "ASS2_FLD_CD",
            "ASS3_FLD_CD",
            "ASS4_FLD_CD",
            "ASS5_FLD_CD"
        ]:

            assist_position = row[assist_field]

            # Only interested in outfield assists
            if assist_position not in (
                "7",
                "8",
                "9"
            ):

                continue

            # Determine individual fielder
            if assist_position == "7":

                player_id = row["POS7_FLD_ID"]

            elif assist_position == "8":

                player_id = row["POS8_FLD_ID"]

            else:

                player_id = row["POS9_FLD_ID"]

            # Count assists by individual player
            if player_id not in game_assists[game_id]:

                game_assists[game_id][player_id] = 0

            game_assists[game_id][player_id] += 1

# --------------------------------------------------
# Build qualifying results
# --------------------------------------------------

results = []

for game_id, players in game_assists.items():

    for player_id, assists in players.items():

        if assists >= 2:

            date = (
                f"{game_id[3:7]}-"
                f"{game_id[7:9]}-"
                f"{game_id[9:11]}"
            )

            results.append(
                {
                    "date": date,
                    "game_id": game_id,
                    "opponent": game_info[game_id]["opponent"],
                    "home_away": game_info[game_id]["home_away"],
                    "player_id": player_id,
                    "assists": assists
                }
            )

# --------------------------------------------------
# Sort chronologically
# --------------------------------------------------

results.sort(
    key=lambda x: x["date"]
)

# --------------------------------------------------
# Output
# --------------------------------------------------

print(
    "\nGames with 2+ assists by one opposing outfielder:\n"
)

for result in results:

    location = (
        "vs"
        if result["home_away"] == "Home"
        else "at"
    )

    print(
        result["date"],
        location,
        result["opponent"],
        result["player_id"],
        result["assists"]
    )
