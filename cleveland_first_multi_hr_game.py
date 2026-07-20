import os
import zipfile
import requests
import pandas as pd
import csv
from collections import defaultdict

# ---------------------------------
# Configuration
# ---------------------------------

TEAM = "CLE"
START_YEAR = 1910
END_YEAR = 2025

OUTPUT_FILE = (
    "cleveland_first_multi_hr_game.csv"
)

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------
# Chadwick Register
# ---------------------------------

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

# ---------------------------------
# Download Retrosheet Files
# ---------------------------------

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

    for file in os.listdir(
        year_dir
    ):

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

# ---------------------------------
# Dictionaries we'll use
# ---------------------------------

career_hr = defaultdict(int)

game_hr = defaultdict(int)

first_multi_hr = {}

results = []
