import re
import statsapi

TEAM = "Cleveland Guardians"

START_YEAR = 2026
END_YEAR = 2026

for year in range(
    START_YEAR,
    END_YEAR + 1
):

    print(f"\nProcessing {year}...")

    schedule = statsapi.schedule(
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        team=114
    )

    print(f"Found {len(schedule)} games.")

    for game in schedule:

        gamePk = game["game_id"]
    
        boxscore = statsapi.get(
            "game",
            {
                "gamePk": gamePk
            }
        )
    
        home_id = boxscore["gameData"]["teams"]["home"]["id"]
    
        if home_id == 114:
        
            info = (
                boxscore["liveData"]
                ["boxscore"]
                ["teams"]
                ["home"]
                ["info"]
            )
        
            opponent = (
                boxscore["gameData"]
                ["teams"]
                ["away"]
                ["abbreviation"]
            )
        
            home_away = "Home"
        
        else:
        
            info = (
                boxscore["liveData"]
                ["boxscore"]
                ["teams"]
                ["away"]
                ["info"]
            )
        
            opponent = (
                boxscore["gameData"]
                ["teams"]
                ["home"]
                ["abbreviation"]
            )
        
            home_away = "Away"
    
        risp = None
        hits = None
        at_bats = None
    
        for section in info:
    
            for field in section.get("fieldList", []):
    
                if field["label"] == "Team RISP":
    
                    risp = field["value"]
    
                    if risp:
    
                        match = re.search(
                            r"(\d+)-for-(\d+)",
                            risp
                        )
    
                        if match:
    
                            hits = int(
                                match.group(1)
                            )
    
                            at_bats = int(
                                match.group(2)
                            )
    
        if home_away == "Home":

            print(
                f"{game['game_date']}  "
                f"{home_away} vs {opponent}  "
                f"RISP={risp}  "
                f"hits={hits}  "
                f"ab={at_bats}"
            )
