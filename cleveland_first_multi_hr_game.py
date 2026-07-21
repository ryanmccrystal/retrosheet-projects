import os
import zipfile
import requests
import pandas as pd
import csv

from collections import defaultdict

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEAM = "CLE"

START_YEAR = 1946
END_YEAR = 1946

OUTPUT_FILE = "cleveland_first_multi_hr_game.csv"

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

# --------------------------------------------------
# Chadwick Register
# --------------------------------------------------

def load_chadwick_register():

    dfs = []

    for letter in "0123456789abcdef":

        url = (
            "https://raw.githubusercontent.com/"
            "chadwickbureau/register/master/"
            f"data/people-{letter}.csv"
        )

        print(f"Loading people-{letter}.csv")

        dfs.append(
            pd.read_csv(
                url,
                low_memory=False
            )
        )

    return pd.concat(
        dfs,
        ignore_index=True
    )


print("\nLoading Chadwick Register...\n")

register = load_chadwick_register()

canonical_name = {}

for _, row in register.iterrows():

    retro_id = row["key_retro"]

    if pd.isna(retro_id):
        continue

    canonical_name[retro_id] = (
        f"{row['name_first']} "
        f"{row['name_last']}"
    )

# --------------------------------------------------
# Download Retrosheet Files
# --------------------------------------------------

event_files = []

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

        z.extractall(
            year_dir
        )

    for file in os.listdir(year_dir):

        if (
            file.endswith(".EVA")
            or file.endswith(".EVN")
        ):

            event_files.append(
                os.path.join(
                    year_dir,
                    file
                )
            )

print(
    f"\nFound {len(event_files)} event files.\n"
)

# --------------------------------------------------
# Track Career HRs
# --------------------------------------------------

career_hr = defaultdict(int)

first_multi_hr = {}

for event_file in event_files:

    current_game_id = None
    current_date = None
    visteam = None
    hometeam = None

    game_hr = defaultdict(int)

    with open(
        event_file,
        encoding="latin-1"
    ) as f:
    
        if os.path.basename(event_file) == "1946CLE.EVA":
            print(f"Reading {event_file}")
    
        current_debug_game = False
        
        for raw_line in f:
        
            line = raw_line.strip()
        
            if line.startswith("id,"):
        
                current_debug_game = (
                    line == "id,CLE194609200"
                )
        
            if current_debug_game:
                print(line)

            # --------------------------
            # New Game
            # --------------------------

            if line.startswith("id,"):

                current_game_id = line.split(",")[1]

                current_date = None
                visteam = None
                hometeam = None

                game_hr.clear()

                continue

            # --------------------------
            # Game Info
            # --------------------------

            if line.startswith("info,date,"):

                current_date = line.split(",")[2]
                continue

            if line.startswith("info,visteam,"):

                visteam = line.split(",")[2]
                continue

            if line.startswith("info,hometeam,"):

                hometeam = line.split(",")[2]
                continue

            # --------------------------
            # Plays
            # --------------------------

            if not line.startswith("play,"):
                continue

            fields = line.split(",")

            batting_team = fields[2]
            batter_id = fields[3]
            event = fields[6]

            # --------------------------
            # DEBUG
            # --------------------------
            
            if line.startswith("info,date,"):
                print("DATE:", line)
            
            if line.startswith("info,visteam,"):
                print("VIS:", line)
            
            if line.startswith("info,hometeam,"):
                print("HOME:", line)

            # --------------------------

            if not event.startswith("HR"):
                continue

            team_abbr = (
                visteam
                if batting_team == "0"
                else hometeam
            )

            opponent = (
                hometeam
                if batting_team == "0"
                else visteam
            )

            home_away = (
                "Away"
                if batting_team == "0"
                else "Home"
            )

            if batter_id == "robie101":
                print(
                    current_date,
                    current_game_id,
                    career_hr[batter_id],
                    event
                )

            # Count ALL career HR
            career_hr[batter_id] += 1

            # Count HR in THIS game
            game_hr[batter_id] += 1

            # First time reaching 2 HR in any game
            if (
                game_hr[batter_id] == 2
                and batter_id not in first_multi_hr
            ):

                # Only SAVE if it happened with Cleveland
                if team_abbr == TEAM:

                    first_multi_hr[batter_id] = {

                        "player":
                            canonical_name.get(
                                batter_id,
                                batter_id
                            ),

                        "date":
                            current_date,

                        "game_id":
                            current_game_id,

                        "opponent":
                            opponent,

                        "home_away":
                            home_away,

                        "career_hr_before":
                            career_hr[batter_id] - 2,

                        "hrs_in_game":
                            2
                    }

                else:

                    # Mark as already having a first
                    # multi-HR game with another team
                    first_multi_hr[batter_id] = None

            # If first career multi-HR game
            # happened with Cleveland,
            # update 3-HR and 4-HR games.
            elif (
                batter_id in first_multi_hr
                and first_multi_hr[batter_id] is not None
                and first_multi_hr[batter_id]["game_id"]
                == current_game_id
            ):

                first_multi_hr[batter_id][
                    "hrs_in_game"
                ] = game_hr[batter_id]

# --------------------------------------------------
# Build Results
# --------------------------------------------------

results = []

for player_id, row in first_multi_hr.items():

    if row is None:
        continue

    row["career_hr_after"] = (
        row["career_hr_before"]
        + row["hrs_in_game"]
    )

    results.append(row)

results.sort(
    key=lambda x: (
        x["career_hr_before"],
        x["date"]
    )
)

# --------------------------------------------------
# Write CSV
# --------------------------------------------------

fieldnames = [

    "player",
    "career_hr_before",
    "date",
    "opponent",
    "home_away",
    "hrs_in_game",
    "career_hr_after",
    "game_id"
]

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(results)

print(f"\nCSV written: {OUTPUT_FILE}")

print(
    f"Found {len(results)} players.\n"
)

print("Top 50:\n")

for row in results[:50]:

    print(
        f"{row['career_hr_before']:>3} | "
        f"{row['player']:<25} | "
        f"{row['date']} | "
        f"{row['opponent']} | "
        f"{row['hrs_in_game']} HR"
    )
