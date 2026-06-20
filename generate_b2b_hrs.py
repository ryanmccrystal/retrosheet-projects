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

# First pass: build player lookup
with open(first_file, encoding="latin-1") as f:

    for line in f:

        line = line.strip()

        if line.startswith("start,"):

            fields = line.split(",")

            player_id = fields[1]
            player_name = fields[2].replace('"', "")

            player_lookup[player_id] = player_name

# Second pass: find HRs
with open(first_file, encoding="latin-1") as f:

    hr_count = 0

    for line in f:

        line = line.strip()

        if not line.startswith("play,"):
            continue

        fields = line.split(",")

        inning = fields[1]
        team = fields[2]
        batter_id = fields[3]
        event = fields[6]

        if event.startswith("HR"):

            batter_name = player_lookup.get(
                batter_id,
                batter_id
            )

            print(
                f"Inning {inning} | Team {team} | {batter_name}"
            )

            hr_count += 1

            if hr_count >= 20:
                break
