import os
import csv
import zipfile
import subprocess
import requests

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEAM = "CLE"

START_YEAR = 1910
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
