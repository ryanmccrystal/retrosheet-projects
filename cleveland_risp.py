import re
import statsapi

TEAM = "Cleveland Guardians"

START_DATE = "2020-07-23"
END_DATE = "2020-09-27"

print("Getting Cleveland schedule...")

schedule = statsapi.schedule(
    start_date=START_DATE,
    end_date=END_DATE,
    team=114
)

print(f"Found {len(schedule)} games.\n")

for game in schedule:

    gamePk = game["game_id"]

    boxscore = statsapi.get(
        "game",
        {
            "gamePk": gamePk
        }
    )

    home_team = boxscore["gameData"]["teams"]["home"]["name"]

    if home_team == TEAM:

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

    for section in info:

        for field in section.get("fieldList", []):

            if field["label"] == "Team RISP":

                risp = field["value"]

    print(
        f"{game['game_date']}  "
        f"{home_away} vs {opponent}  "
        f"{risp}"
    )
