import os
import zipfile
import requests

DATA_DIR = "data"
ZIP_FILE = os.path.join(DATA_DIR, "2025eve.zip")

os.makedirs(DATA_DIR, exist_ok=True)

# Download only if missing
if not os.path.exists(ZIP_FILE):
    print("Downloading Retrosheet 2025 event files...")

    url = "https://www.retrosheet.org/events/2025eve.zip"
    r = requests.get(url)
    r.raise_for_status()

    with open(ZIP_FILE, "wb") as f:
        f.write(r.content)

    print("Download complete.")

# Extract
with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(DATA_DIR)

# Find event files
event_files = sorted([
    f for f in os.listdir(DATA_DIR)
    if f.endswith(".EVA") or f.endswith(".EVN")
])

print(f"Found {len(event_files)} event files")

# Open first file
first_file = os.path.join(DATA_DIR, event_files[0])

print(f"\nReading: {event_files[0]}\n")

player_lookup = {}

with open(first_file, encoding="latin-1") as f:

    for line in f:

        line = line.strip()

        if line.startswith("start,"):

            fields = line.split(",")

            player_id = fields[1]
            player_name = fields[2].replace('"', "")

            player_lookup[player_id] = player_name

streak = []

current_inning = None
current_team = None

print("\nBack-to-back HR streaks found:\n")

with open(first_file, encoding="latin-1") as f:

    for line in f:

        line = line.strip()

        if not line.startswith("play,"):
            continue

        fields = line.split(",")

        inning = fields[1]
        batting_team = fields[2]
        batter_id = fields[3]
        event = fields[6]

        batter_name = player_lookup.get(
            batter_id,
            batter_id
        )

        is_hr = event.startswith("HR")

        # New inning or new batting team
        if (
            inning != current_inning
            or batting_team != current_team
        ):

            if len(streak) >= 2:

                print(
                    f"Inning {current_inning} "
                    f"Team {current_team}: "
                    + ", ".join(streak)
                )

            streak = []

            current_inning = inning
            current_team = batting_team

        if is_hr:

            streak.append(batter_name)

        else:

            if len(streak) >= 2:

                print(
                    f"Inning {current_inning} "
                    f"Team {current_team}: "
                    + ", ".join(streak)
                )

            streak = []

# Catch streak at EOF
if len(streak) >= 2:

    print(
        f"Inning {current_inning} "
        f"Team {current_team}: "
        + ", ".join(streak)
    )
