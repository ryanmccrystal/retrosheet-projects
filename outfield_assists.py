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
# Test Chadwick
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
            "1986",
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

        if row["GAME_ID"][0:3] != TEAM:
            continue
        
        if row["BAT_HOME_ID"] != "1":
            continue
        
        if (
            row["ASS1_FLD_CD"]
            or row["ASS2_FLD_CD"]
            or row["ASS3_FLD_CD"]
            or row["ASS4_FLD_CD"]
            or row["ASS5_FLD_CD"]
        ):

            print(row)
