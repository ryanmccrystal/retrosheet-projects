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

import csv

results = []

# Summary counters
streak_counts = {}

for event_file in event_files:

    filepath = os.path.join(DATA_DIR, event_file)

    current_game_id = None
    current_date = None
    visteam = None
    hometeam = None
    gametype = None

    player_lookup = {}

    current_inning = None
    current_team = None
    streak = []

    def save_streak():
        if len(streak) < 2:
            return

        team_abbr = visteam if current_team == "0" else hometeam
        opponent = hometeam if current_team == "0" else visteam

        row = {
            "date": current_date,
            "game_id": current_game_id,
            "team": team_abbr,
            "opponent": opponent,
            "inning": current_inning,
            "count": len(streak),
            "player_1": "",
            "player_2": "",
            "player_3": "",
            "player_4": "",
            "player_5": ""
        }

        for i, player in enumerate(streak[:5]):
            row[f"player_{i+1}"] = player

        results.append(row)

        streak_counts[len(streak)] = (
            streak_counts.get(len(streak), 0) + 1
        )

    with open(filepath, encoding="latin-1") as f:

        for raw_line in f:

            line = raw_line.strip()

            # New game
            if line.startswith("id,"):

                save_streak()

                current_game_id = line.split(",")[1]

                current_date = None
                visteam = None
                hometeam = None
                gametype = None

                player_lookup = {}

                current_inning = None
                current_team = None
                streak = []

                continue

            # Game metadata
            if line.startswith("info,date,"):
                current_date = line.split(",")[2]
                continue

            if line.startswith("info,visteam,"):
                visteam = line.split(",")[2]
                continue

            if line.startswith("info,hometeam,"):
                hometeam = line.split(",")[2]
                continue

            if line.startswith("info,gametype,"):
                gametype = line.split(",")[2]
                continue

            # Player lookup
            if line.startswith("start,"):

                fields = line.split(",")

                player_lookup[fields[1]] = (
                    fields[2].replace('"', '')
                )

                continue

            if line.startswith("sub,"):

                fields = line.split(",")

                player_lookup[fields[1]] = (
                    fields[2].replace('"', '')
                )

                continue

            # Ignore non-regular season games
            if gametype != "regular":
                continue

            # Play records
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

            # inning/team changed
            if (
                inning != current_inning
                or batting_team != current_team
            ):

                save_streak()

                streak = []

                current_inning = inning
                current_team = batting_team

            if event.startswith("HR"):

                streak.append(batter_name)

            else:

                save_streak()

                streak = []

        # End of file
        save_streak()

# Write CSV

output_file = "b2b_hr_streaks_2025.csv"

fieldnames = [
    "date",
    "game_id",
    "team",
    "opponent",
    "inning",
    "count",
    "player_1",
    "player_2",
    "player_3",
    "player_4",
    "player_5"
]

with open(output_file, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(results)

print(f"\nCSV written: {output_file}")

print(f"\nTotal streaks: {len(results)}\n")

for length in sorted(streak_counts):

    print(
        f"{length}-player streaks: "
        f"{streak_counts[length]}"
    )

if streak_counts:

    print(
        f"\nLongest streak: "
        f"{max(streak_counts)}"
    )
