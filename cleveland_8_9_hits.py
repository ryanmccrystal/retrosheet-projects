import os
import zipfile
import requests

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEAM = "CLE"

START_YEAR = 2000
END_YEAR = 2000

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
    f"\nFound {len(event_files)} event files.\n"
)

# --------------------------------------------------
# Find Cleveland Games
# --------------------------------------------------

game_count = 0

for event_file in sorted(event_files):

    game_id = None
    game_date = None
    visteam = None
    hometeam = None

    with open(
        event_file,
        encoding="latin-1"
    ) as f:

        for raw_line in f:

            line = raw_line.strip()

            if line.startswith("id,"):

                # Print previous game
                if (
                    game_id
                    and
                    (
                        visteam == TEAM
                        or hometeam == TEAM
                    )
                ):

                    opponent = (
                        visteam
                        if hometeam == TEAM
                        else hometeam
                    )

                    home_away = (
                        "Home"
                        if hometeam == TEAM
                        else "Away"
                    )

                    game_count += 1

                    print(
                        f"{game_date}  "
                        f"{game_id}  "
                        f"{home_away}  "
                        f"vs {opponent}"
                    )

                # Start new game
                game_id = line.split(",")[1]

                game_date = None
                visteam = None
                hometeam = None

                continue

            if line.startswith("info,date,"):

                game_date = line.split(",")[2]

                continue

            if line.startswith("info,visteam,"):

                visteam = line.split(",")[2]

                continue

            if line.startswith("info,hometeam,"):

                hometeam = line.split(",")[2]

                continue

    # Print final game in file
    if (
        game_id
        and
        (
            visteam == TEAM
            or hometeam == TEAM
        )
    ):

        opponent = (
            visteam
            if hometeam == TEAM
            else hometeam
        )

        home_away = (
            "Home"
            if hometeam == TEAM
            else "Away"
        )

        game_count += 1

        print(
            f"{game_date}  "
            f"{game_id}  "
            f"{home_away}  "
            f"vs {opponent}"
        )

print(
    f"\nFound {game_count} Cleveland games."
)
