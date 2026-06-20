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

results = []

for event_file in event_files:

    filepath = os.path.join(DATA_DIR, event_file)

    player_lookup = {}

    game_date = None
    visteam = None
    hometeam = None

    current_inning = None
    current_team = None

    streak = []

    # Build player lookup and gather game info
    with open(filepath, encoding="latin-1") as f:

        for line in f:

            line = line.strip()

            if line.startswith("info,date,"):
                game_date = line.split(",")[2]

            elif line.startswith("info,visteam,"):
                visteam = line.split(",")[2]

            elif line.startswith("info,hometeam,"):
                hometeam = line.split(",")[2]

            elif line.startswith("start,"):

                fields = line.split(",")

                player_lookup[fields[1]] = (
                    fields[2].replace('"', '')
                )

    # Scan plays
    with open(filepath, encoding="latin-1") as f:

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

            # inning/team changed
            if (
                inning != current_inning
                or batting_team != current_team
            ):

                if len(streak) >= 2:

                    results.append({
                        "date": game_date,
                        "team": team_abbr,
                        "opponent": opponent,
                        "inning": current_inning,
                        "players": streak.copy()
                    })

                streak = []

                current_inning = inning
                current_team = batting_team

            if event.startswith("HR"):

                streak.append(batter_name)

            else:

                if len(streak) >= 2:

                    results.append({
                        "date": game_date,
                        "team": team_abbr,
                        "opponent": opponent,
                        "inning": current_inning,
                        "players": streak.copy()
                    })

                streak = []

        if len(streak) >= 2:

            results.append({
                "date": game_date,
                "team": team_abbr,
                "opponent": opponent,
                "inning": current_inning,
                "players": streak.copy()
            })

print(f"\nFound {len(results)} streaks\n")

for row in results[:25]:

    print(
        f"{row['date']} | "
        f"{row['team']} vs {row['opponent']} | "
        f"Inning {row['inning']} | "
        f"{', '.join(row['players'])}"
    )
