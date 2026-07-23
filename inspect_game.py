import json
import statsapi

# Pick any 2020 game.
GAME_PK = 631042   # Cleveland @ White Sox, Aug. 7, 2020

print("Downloading game...")

game = statsapi.get(
    "game",
    {
        "gamePk": GAME_PK
    }
)

print("Saving full JSON...")

with open(
    "game.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        game,
        f,
        indent=2
    )

print("Done.")
print("Created: game.json")
