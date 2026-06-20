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

for event_file in event_files:

    filepath = os.path.join(DATA_DIR, event_file)

    print(f"\n--- {event_file} ---")

    game_count = 0

    with open(filepath, encoding="latin-1") as f:

        for line in f:

            line = line.strip()

            if line.startswith("id,"):

                print(line)

                game_count += 1

                if game_count >= 5:
                    break
