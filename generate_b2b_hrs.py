import os
import zipfile
import requests

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

event_files = []

for year in range(1980, 1988):

    zip_file = os.path.join(DATA_DIR, f"{year}eve.zip")
    year_dir = os.path.join(DATA_DIR, str(year))

    if not os.path.exists(zip_file):

        print(f"Downloading {year}...")

        url = f"https://www.retrosheet.org/events/{year}eve.zip"

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

        if file.endswith(".EVA") or file.endswith(".EVN"):

            event_files.append(
                os.path.join(year_dir, file)
            )

print(f"Found {len(event_files)} event files")

import csv

results = []

# Summary counters
streak_counts = {}

for event_file in event_files:

    filepath = event_file

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

        # Cleveland only
        if team_abbr != "CLE":
            return

        home_away = (
            "Away"
            if current_team == "0"
            else "Home"
        )

        row = {
            "year": current_date[:4],
            "date": current_date,
            "game_id": current_game_id,
            "opponent": opponent,
            "home_away": home_away,
            "inning": current_inning,
            "streak": len(streak)
        }

        for i, player in enumerate(streak):
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

            # Player lookup
            if line.startswith("start,"):

                if "thorna001" in line:
                    print(line)

                fields = line.split(",")

                player_lookup[fields[1]] = (
                    fields[2].replace('"', '')
                )

                continue

            if line.startswith("sub,"):

                if "thorna001" in line:
                    print(line)

                fields = line.split(",")

                player_lookup[fields[1]] = (
                    fields[2].replace('"', '')
                )

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

            # No Play does not end a streak
            if event == "NP":
                continue

            if event.startswith("HR"):

                streak.append(batter_name)

            else:

                save_streak()

                streak = []

        # End of file
        save_streak()

max_streak = max(
    row["streak"]
    for row in results
)

# Write CSV

output_file = "cleveland_hr_streaks_1910_2025.csv"

fieldnames = [
    "year",
    "date",
    "game_id",
    "opponent",
    "home_away",
    "inning",
    "streak"
]

for i in range(1, max_streak + 1):
    fieldnames.append(f"player_{i}")

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

from collections import Counter

year_counts = Counter()

for row in results:
    year_counts[row["year"]] += 1

print("\nStreaks by year:\n")

for year in sorted(year_counts):
    print(f"{year}: {year_counts[year]}")

from collections import Counter

pair_counts = Counter()

for row in results:

    players = []

    for key, value in row.items():

        if key.startswith("player_") and value:
            players.append(value)

    # Count consecutive pairs only
    for i in range(len(players) - 1):

        pair = tuple(
            sorted([
                players[i],
                players[i + 1]
            ])
        )

        pair_counts[pair] += 1

print("\nTop Cleveland HR Pairs:\n")

for pair, count in pair_counts.most_common(50):

    print(
        f"{pair[0]} / {pair[1]} - {count}"
    )

from collections import defaultdict

partner_counts = defaultdict(set)

for pair in pair_counts:

    player1, player2 = pair

    partner_counts[player1].add(player2)
    partner_counts[player2].add(player1)

print("\nMost Unique HR Partners:\n")

leaders = sorted(
    partner_counts.items(),
    key=lambda x: len(x[1]),
    reverse=True
)

for player, partners in leaders[:50]:

    print(
        f"{player} - {len(partners)}"
    )
