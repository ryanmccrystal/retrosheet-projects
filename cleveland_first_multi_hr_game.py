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
            f"https://www.retrosheet.org/"
            f"events/{year}eve.zip"
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
# PASS 1
# Collect every MLB HR
# --------------------------------------------------

all_home_runs = []

for event_file in event_files:

    if not event_file.endswith("1946CLE.EVA"):
        continue

    print(f"\nReading {event_file}\n")

    current_game_id = None
    current_date = None
    visteam = None
    hometeam = None

    with open(
        event_file,
        encoding="latin-1"
    ) as f:

        for i, raw_line in enumerate(f):

            if i >= 30:
                break

            print(raw_line.rstrip())

    break

        for raw_line in f:

            line = raw_line.strip()

            if line.startswith("id,CLE194609200"):
                print("FOUND GAME")

            if line.startswith("id,"):

                current_game_id = (
                    line.split(",")[1]
                )

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

            batting_team = fields[2]
            batter_id = fields[3]
            event = fields[6]
            
            if (
                current_game_id == "CLE194609200"
                and batter_id == "robie101"
            ):
                print(
                    f"{current_date} | "
                    f"Inning {fields[1]} | "
                    f"Batting Team {batting_team} | "
                    f"{event}"
                )

            fields = line.split(",")

            batting_team = fields[2]
            batter_id = fields[3]
            event = fields[6]

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

            all_home_runs.append({

                "date":
                    current_date,

                "game_id":
                    current_game_id,

                "batter":
                    batter_id,

                "player":
                    canonical_name.get(
                        batter_id,
                        batter_id
                    ),

                "team":
                    team_abbr,

                "opponent":
                    opponent,

                "home_away":
                    home_away
            })

print(
    f"Collected {len(all_home_runs)} HR.\n"
)

all_home_runs.sort(
    key=lambda x: x["game_id"][3:]
)

print("\nFirst 20 games after sorting:\n")

for hr in all_home_runs[:20]:

    print(hr["game_id"])

# --------------------------------------------------
# PASS 2
# Process HR chronologically
# --------------------------------------------------

career_hr = defaultdict(int)
game_hr = defaultdict(int)

first_multi_hr = {}

for hr in all_home_runs:

    batter = hr["batter"]

    game_key = (
        hr["game_id"],
        batter
    )

    career_before = career_hr[batter]

    career_hr[batter] += 1
    game_hr[game_key] += 1

    # First career multi-HR game
    if (
        game_hr[game_key] == 2
        and batter not in first_multi_hr
    ):

        if hr["team"] == TEAM:

            first_multi_hr[batter] = {

                "player":
                    hr["player"],

                "career_hr_before":
                    career_before - 1,

                "date":
                    hr["date"],

                "game_id":
                    hr["game_id"],

                "opponent":
                    hr["opponent"],

                "home_away":
                    hr["home_away"],

                "hrs_in_game":
                    2
            }

        else:

            # First multi-HR game occurred
            # with another club.
            first_multi_hr[batter] = None

    # Update 3-HR and 4-HR games
    elif (
        batter in first_multi_hr
        and first_multi_hr[batter] is not None
        and first_multi_hr[batter]["game_id"]
        == hr["game_id"]
    ):

        first_multi_hr[batter][
            "hrs_in_game"
        ] = game_hr[game_key]

# --------------------------------------------------
# Build Results
# --------------------------------------------------

results = []

for row in first_multi_hr.values():

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
        x["date"],
        x["player"]
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

print(
    f"\nCSV written: {OUTPUT_FILE}"
)

print(
    f"\nFound {len(results)} players.\n"
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
