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

START_YEAR = 1994
END_YEAR = 2025

OUTPUT_FILE = "cleveland_8_9_hits.csv"

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

    if pd.isna(row["key_retro"]):
        continue

    canonical_name[row["key_retro"]] = (
        f"{row['name_first']} "
        f"{row['name_last']}"
    )

# --------------------------------------------------
# Download Event Files
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
# Search Games
# --------------------------------------------------

results = []

for event_file in event_files:

    current_game = None
    current_date = None

    visteam = None
    hometeam = None

    starters = {}

    hits = defaultdict(int)

    with open(
        event_file,
        encoding="latin-1"
    ) as f:

        for raw_line in f:

            line = raw_line.strip()

            # --------------------------
            # New Game
            # --------------------------

            if line.startswith("id,"):

                # Save previous game
                if (
                    hometeam == TEAM
                    or visteam == TEAM
                ):

                    if (
                        8 in starters
                        and 9 in starters
                    ):

                        total = (
                            hits[starters[8]["id"]]
                            +
                            hits[starters[9]["id"]]
                        )

                        print(
                            current_date,
                            starters[8]["name"],
                            hits[starters[8]["id"]],
                            starters[9]["name"],
                            hits[starters[9]["id"]],
                            total
                        )
                        
                        if total >= 7:

                            opponent = (
                                visteam
                                if hometeam == TEAM
                                else hometeam
                            )

                            home_away = (
                                "Home"
                                if hometeam == TEAM
                                else "Away"
                            )

                            results.append({

                                "date":
                                    current_date,

                                "game_id":
                                    current_game,

                                "opponent":
                                    opponent,

                                "home_away":
                                    home_away,

                                "player_8":
                                    starters[8]["name"],

                                "hits_8":
                                    hits[
                                        starters[8]["id"]
                                    ],

                                "player_9":
                                    starters[9]["name"],

                                "hits_9":
                                    hits[
                                        starters[9]["id"]
                                    ],

                                "combined_hits":
                                    total
                            })

                current_game = line.split(",")[1]

                current_date = None
                visteam = None
                hometeam = None

                starters = {}
                hits = defaultdict(int)

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
            # Starting Lineups
            # --------------------------

            if line.startswith("start,"):

                fields = line.split(",")

                player_id = fields[1]

                batting_order = int(fields[4])

                if batting_order in (8, 9):

                    starters[batting_order] = {

                        "id":
                            player_id,

                        "name":
                            canonical_name.get(
                                player_id,
                                player_id
                            )
                    }

                continue

                # --------------------------
                # Play Records
                # --------------------------
    
                if not line.startswith("play,"):
                    continue
    
                fields = line.split(",")
    
                batter_id = fields[3]
                event = fields[6]
    
                # Count hits by the starting
                # #8 and #9 hitters only.
                if event.startswith(("S", "D", "T", "HR")):
    
                    for slot in (8, 9):
    
                        if (
                            slot in starters
                            and batter_id
                            == starters[slot]["id"]
                        ):
    
                            hits[batter_id] += 1
    
        # --------------------------------------------------
        # Save final game in file
        # --------------------------------------------------
    
        if (
            hometeam == TEAM
            or visteam == TEAM
        ):
    
            if (
                8 in starters
                and 9 in starters
            ):
    
                total = (
                    hits[starters[8]["id"]]
                    +
                    hits[starters[9]["id"]]
                )
    
                if total >= 8:
    
                    opponent = (
                        visteam
                        if hometeam == TEAM
                        else hometeam
                    )
    
                    home_away = (
                        "Home"
                        if hometeam == TEAM
                        else "Away"
                    )
    
                    results.append({
    
                        "date":
                            current_date,
    
                        "game_id":
                            current_game,
    
                        "opponent":
                            opponent,
    
                        "home_away":
                            home_away,
    
                        "player_8":
                            starters[8]["name"],
    
                        "hits_8":
                            hits[
                                starters[8]["id"]
                            ],
    
                        "player_9":
                            starters[9]["name"],
    
                        "hits_9":
                            hits[
                                starters[9]["id"]
                            ],
    
                        "combined_hits":
                            total
                    })
    
    # --------------------------------------------------
    # Sort Results
    # --------------------------------------------------
    
    results.sort(
    
        key=lambda x: (
    
            x["combined_hits"],
            x["date"]
        ),
    
        reverse=True
    )
    
    # --------------------------------------------------
    # Write CSV
    # --------------------------------------------------
    
    fieldnames = [
    
        "date",
        "game_id",
        "opponent",
        "home_away",
        "player_8",
        "hits_8",
        "player_9",
        "hits_9",
        "combined_hits"
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
        f"\nFound {len(results)} qualifying games.\n"
    )
    
    for row in results:
    
        print(
            f"{row['date']}  "
            f"{row['player_8']} ({row['hits_8']}) + "
            f"{row['player_9']} ({row['hits_9']}) = "
            f"{row['combined_hits']}"
        )

          
