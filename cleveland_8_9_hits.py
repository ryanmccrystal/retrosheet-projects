import os
import zipfile
import requests

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEAM = "CLE"

START_YEAR = 1910
END_YEAR = 2025

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

results = []

for event_file in sorted(event_files):

    game_id = None
    game_date = None
    visteam = None
    hometeam = None
    starters = {}
    hits = {}
    home_runs = {}

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
                    
                    combined_hits = sum(hits.values())
                    combined_home_runs = sum(home_runs.values())

                    if (
                        combined_hits >= 7
                        and combined_home_runs >= 3
                    ):

                        players = sorted(
                            starters.items(),
                            key=lambda x: x[1]["order"]
                        )
                    
                        p8_id, p8 = players[0]
                        p9_id, p9 = players[1]
                    
                        results.append({
                    
                            "date": game_date,
                    
                            "game_id": game_id,
                    
                            "opponent": opponent,
                    
                            "home_away": home_away,
                    
                            "player_8": p8["name"],
                    
                            "hits_8": hits.get(p8_id, 0),
                    
                            "player_9": p9["name"],
                    
                            "hits_9": hits.get(p9_id, 0),
                    
                            "combined_hits": combined_hits,

                            "home_runs_8": home_runs.get(p8_id, 0),

                            "home_runs_9": home_runs.get(p9_id, 0),
                            
                            "combined_home_runs": combined_home_runs,
                    
                        })

                # Start new game
                game_id = line.split(",")[1]
                
                game_date = None
                visteam = None
                hometeam = None
                
                starters = {}
                hits = {}
                home_runs = {}
                
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

            # --------------------------
            # Starting Lineups
            # --------------------------
            
            if line.startswith("start,"):

                fields = line.split(",")
            
                player_id = fields[1]
                player_name = fields[2].strip('"')
                team = fields[3]
                batting_order = int(fields[4])
            
                # Keep only Cleveland's starting #8 and #9 hitters
                if (
                    (visteam == TEAM and team == "0")
                    or
                    (hometeam == TEAM and team == "1")
                ):
            
                    if batting_order in (8, 9):
            
                        starters[player_id] = {
            
                            "name": player_name,
            
                            "order": batting_order
            
                        }
            
                continue

            # --------------------------
            # Play Records
            # --------------------------
            
            if not line.startswith("play,"):
                continue
            
            fields = line.split(",")
            
            batter_id = fields[3]
            event = fields[6]
            
            if batter_id in starters:

                if event.startswith(("S", "D", "T", "HR")):
            
                    hits[batter_id] = hits.get(
                        batter_id,
                        0
                    ) + 1
            
                if event.startswith("HR"):
            
                    home_runs[batter_id] = home_runs.get(
                        batter_id,
                        0
                    ) + 1
            
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
        
        combined_hits = sum(hits.values())
        combined_home_runs = sum(home_runs.values())

        if (
            combined_hits >= 7
            and combined_home_runs >= 3
        ):

            players = sorted(
                starters.items(),
                key=lambda x: x[1]["order"]
            )
        
            p8_id, p8 = players[0]
            p9_id, p9 = players[1]
        
            results.append({
        
                "date": game_date,
        
                "game_id": game_id,
        
                "opponent": opponent,
        
                "home_away": home_away,
        
                "player_8": p8["name"],
        
                "hits_8": hits.get(p8_id, 0),
        
                "player_9": p9["name"],
        
                "hits_9": hits.get(p9_id, 0),
        
                "combined_hits": combined_hits,

                "home_runs_8": home_runs.get(p8_id, 0),

                "home_runs_9": home_runs.get(p9_id, 0),
                
                "combined_home_runs": combined_home_runs,
        
            })

print(f"\nFound {len(results)} qualifying games.\n")

print(
    f"{row['date']}  "
    f"{row['player_8']} "
    f"{row['hits_8']} H, {row['home_runs_8']} HR | "
    f"{row['player_9']} "
    f"{row['hits_9']} H, {row['home_runs_9']} HR | "
    f"Totals: {row['combined_hits']} H, "
    f"{row['combined_home_runs']} HR"
)
