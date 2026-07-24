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
END_YEAR = 2020

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

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

print(
    f"\nFound {len(event_files)} event files."
)

print("\nTesting Chadwick...\n")

sample_file = event_files[0]

sample_dir = os.path.dirname(sample_file)

sample_name = os.path.basename(sample_file)

result = subprocess.run(
    [
        "cwevent",
        "-y",
        "2020",
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

    if row["GAME_ID"] != current_game:

        print(
            current_game,
            risp_hits,
            "for",
            risp_ab
        )

        current_game = row["GAME_ID"]

        risp_ab = 0
        risp_hits = 0

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

    print(
        current_game,
        risp_hits,
        "for",
        risp_ab
    )
