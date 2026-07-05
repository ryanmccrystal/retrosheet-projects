import os
import zipfile
import requests
import pandas as pd
import csv

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
            pd.read_csv(url, low_memory=False)
        )

    return pd.concat(
        dfs,
        ignore_index=True
    )


TEAM = "CLE"
START_YEAR = 1962
END_YEAR = 2025

OUTPUT_FILE = (
    "cleveland_hr_triple_pairs_"
    f"{START_YEAR}_{END_YEAR}.csv"
)

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

event_files = []

for year in range(START_YEAR, END_YEAR + 1):

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
            f"https://www.retrosheet.org/"
            f"events/{year}eve.zip"
        )

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
    f"Found {len(event_files)} event files"
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

results = []

for event_file in event_files:

    current_game_id = None
    current_date = None
    visteam = None
    hometeam = None

    current_inning = None
    current_team = None

    previous_pa = None

    with open(event_file, encoding="latin-1") as f:

        for raw_line in f:

            line = raw_line.strip()

            if line.startswith("id,"):

                current_game_id = (
                    line.split(",")[1]
                )

                current_date = None
                visteam = None
                hometeam = None

                current_inning = None
                current_team = None

                previous_pa = None

                continue

            if line.startswith("info,date,"):

                current_date = (
                    line.split(",")[2]
                )

                continue

            if line.startswith("info,visteam,"):

                visteam = (
                    line.split(",")[2]
                )

                continue

            if line.startswith("info,hometeam,"):

                hometeam = (
                    line.split(",")[2]
                )

                continue

            if not line.startswith("play,"):
                continue

            fields = line.split(",")

            inning = fields[1]
            batting_team = fields[2]
            batter_id = fields[3]
            event = fields[6]

            team_abbr = (
                visteam
                if batting_team == "0"
                else hometeam
            )

            if team_abbr != TEAM:
                continue

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

            if (
                inning != current_inning
                or batting_team != current_team
            ):

                previous_pa = None

                current_inning = inning
                current_team = batting_team

            # No Play does not count as a PA
            if event == "NP":
                continue

            result = None

            if event.startswith("HR"):

                result = "HR"

            elif event.startswith("T"):

                result = "3B"

            if result is None:

                previous_pa = None
                continue

            current_pa = {

                "year": current_date[:4],
                "date": current_date,
                "game_id": current_game_id,
                "opponent": opponent,
                "home_away": home_away,
                "inning": inning,

                "player": canonical_name.get(
                    batter_id,
                    batter_id
                ),

                "result": result
            }

            if previous_pa is not None:

                if (
                    previous_pa["result"] !=
                    current_pa["result"]
                ):

                    results.append({

                        "year":
                            current_pa["year"],

                        "date":
                            current_pa["date"],

                        "game_id":
                            current_pa["game_id"],

                        "opponent":
                            current_pa["opponent"],

                        "home_away":
                            current_pa["home_away"],

                        "inning":
                            current_pa["inning"],

                        "player_1":
                            previous_pa["player"],

                        "result_1":
                            previous_pa["result"],

                        "player_2":
                            current_pa["player"],

                        "result_2":
                            current_pa["result"]
                    })

            previous_pa = current_pa

fieldnames = [

    "year",
    "date",
    "game_id",
    "opponent",
    "home_away",
    "inning",
    "player_1",
    "result_1",
    "player_2",
    "result_2"
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

print(
    f"\nCSV written: {OUTPUT_FILE}"
)

print(
    f"\nFound {len(results)} "
    "HR/Triple pairs.\n"
)

for row in results:

    print(
        f"{row['date']} | "
        f"{row['opponent']} | "
        f"{row['home_away']} | "
        f"Inning {row['inning']}"
    )

    print(
        f"   {row['player_1']} "
        f"({row['result_1']})"
    )

    print(
        f"   {row['player_2']} "
        f"({row['result_2']})"
    )

    print()

# ----------------------------------------------------
# Summary by Year
# ----------------------------------------------------

from collections import Counter

year_counts = Counter()

for row in results:

    year_counts[row["year"]] += 1

print("\nPairs by Year\n")

for year in sorted(year_counts):

    print(
        f"{year}: "
        f"{year_counts[year]}"
    )

# ----------------------------------------------------
# Player Leaderboard
# ----------------------------------------------------

player_counts = Counter()

for row in results:

    player_counts[row["player_1"]] += 1
    player_counts[row["player_2"]] += 1

print("\nMost HR/Triple Pair Appearances\n")

for player, count in player_counts.most_common(50):

    print(
        f"{player} - {count}"
    )

# ----------------------------------------------------
# Pair Leaderboard
# ----------------------------------------------------

pair_counts = Counter()

for row in results:

    pair = tuple(sorted([
        row["player_1"],
        row["player_2"]
    ]))

    pair_counts[pair] += 1

print("\nMost Frequent HR/Triple Pairs\n")

for pair, count in pair_counts.most_common(50):

    print(
        f"{pair[0]} / "
        f"{pair[1]} - "
        f"{count}"
    )
