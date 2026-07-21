import os
import zipfile
import requests

DATA_DIR = "data"
YEAR = 1946

os.makedirs(DATA_DIR, exist_ok=True)

zip_file = os.path.join(DATA_DIR, f"{YEAR}eve.zip")
year_dir = os.path.join(DATA_DIR, str(YEAR))

if not os.path.exists(zip_file):
    url = f"https://www.retrosheet.org/events/{YEAR}eve.zip"
    r = requests.get(url)
    r.raise_for_status()

    with open(zip_file, "wb") as f:
        f.write(r.content)

os.makedirs(year_dir, exist_ok=True)

with zipfile.ZipFile(zip_file, "r") as z:
    z.extractall(year_dir)

print("1946 Cleveland home games:\n")

target_game = "CLE194609210"

for filename in sorted(os.listdir(year_dir)):

    if not (filename.endswith(".EVA") or filename.endswith(".EVN")):
        continue

    path = os.path.join(year_dir, filename)

    in_game = False

    with open(path, encoding="latin-1") as f:

        for line in f:

            line = line.rstrip()

            if line.startswith("id,"):
                in_game = (line[3:] == target_game)

            if in_game:
                print(line)
