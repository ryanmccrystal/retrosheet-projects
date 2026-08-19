import os
import csv
import zipfile
import subprocess
import requests

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEAM = "CLE"

START_YEAR = 1901
END_YEAR = 2025

STAT = "RBI"
INNINGS = 2
MIN_STAT = 5

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

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

games = {}

for event_file in event_files:

    sample_dir = os.path.dirname(event_file)

    sample_name = os.path.basename(event_file)

    year = sample_name[:4]

    print(
        f"Processing {sample_name}"
    )

    result = subprocess.run(
        [
            "cwevent",
            "-y",
            year,
            "-n",
            "-f",
            "0,1,2,3,10,29,43",
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

        # ------------------------------------------
        # Only count first two innings
        # ------------------------------------------

        if int(row["INN_CT"]) > INNINGS:
            continue

        game_id = row["GAME_ID"]

        # ------------------------------------------
        # Create game entry
        # ------------------------------------------

        if game_id not in games:

            games[game_id] = {}
        
        player_id = row["BAT_ID"]
        
        if player_id not in games[game_id]:
        
            games[game_id][player_id] = 0
        
        games[game_id][player_id] += int(
            row["RBI_CT"]
        )

# --------------------------------------------------
# Find qualifying performances
# --------------------------------------------------

results = []

for game_id, players in games.items():

    for player_id, rbi in players.items():

        if rbi >= MIN_STAT:

            date = (
                f"{game_id[3:7]}-"
                f"{game_id[7:9]}-"
                f"{game_id[9:11]}"
            )

            results.append(
                {
                    "date": date,
                    "game_id": game_id,
                    "player_id": player_id,
                    "rbi": rbi
                }
            )

# --------------------------------------------------
# Sort results
# --------------------------------------------------

results.sort(
    key=lambda x: (
        -x["rbi"],
        x["date"]
    )
)

# --------------------------------------------------
# Output
# --------------------------------------------------

print(
    "\nCleveland hitters with "
    f"{MIN_STAT}+ {STAT} through "
    f"{INNINGS} innings:\n"
)

for result in results:

    print(
        result["date"],
        result["player_id"],
        result["rbi"]
    )
