import os
import zipfile
import requests

DATA_DIR = "data"
ZIP_FILE = os.path.join(DATA_DIR, "2025eve.zip")

os.makedirs(DATA_DIR, exist_ok=True)

url = "https://www.retrosheet.org/events/2025eve.zip"

print("Downloading Retrosheet 2025 event files...")

r = requests.get(url)
r.raise_for_status()

with open(ZIP_FILE, "wb") as f:
    f.write(r.content)

print("Extracting files...")

with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(DATA_DIR)

print("Done.")

event_files = [
    f for f in os.listdir(DATA_DIR)
    if f.endswith(".EVN") or f.endswith(".EVA")
]

print(f"\nFound {len(event_files)} event files:\n")

for f in sorted(event_files)[:10]:
    print(f)
