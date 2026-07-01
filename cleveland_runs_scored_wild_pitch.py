import os
import zipfile
import requests
import pandas as pd

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

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

event_files = []

for year in range(2021, 2026):

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
    f"\nFound {len(event_files)} event files\n"
)

wild_pitch_events = []

for event_file in event_files:

    current_game_id = None
    current_date = None
    visteam = None
    hometeam = None

    with open(event_file, encoding="latin-1") as f:

        for raw_line in f:

            line = raw_line.strip()

            if line.startswith("id,"):

                current_game_id = line.split(",")[1]
                continue

            if line.startswith("info,date,"):

                current_date = line.split(",")[2]
                continue

            if line.startswith("info,visteam,"):

                visteam = line.split(",")[2]
                continue

            if line.startswith("info,hometeam,"):

                hometeam = line.split(",")[2]
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

            if team_abbr != "CLE":
                continue

            if "WP" not in event:
                continue

            wild_pitch_events.append({
                "date": current_date,
                "game_id": current_game_id,
                "inning": inning,
                "batter": canonical_name.get(
                    batter_id,
                    batter_id
                ),
                "event": event
            })

print(
    f"\nFound {len(wild_pitch_events)} Cleveland batting plays containing WP.\n"
)

for play in wild_pitch_events:

    print(
        f"{play['date']} | "
        f"{play['game_id']} | "
        f"Inning {play['inning']} | "
        f"{play['batter']} | "
        f"{play['event']}"
    )
