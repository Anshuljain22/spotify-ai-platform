import json
import os

DATA_DIR = "data/raw"

files = [
    "profile.json",
    "top_artists.json",
    "top_tracks.json",
    "recently_played.json",
    "playlists.json"
]

def inspect(obj, level=0, max_level=2):
    indent = "  " * level

    if level > max_level:
        return

    if isinstance(obj, dict):
        for key, value in obj.items():
            print(f"{indent}{key}: {type(value).__name__}")

            if isinstance(value, (dict, list)):
                inspect(value, level + 1, max_level)

    elif isinstance(obj, list):
        print(f"{indent}items: {len(obj)}")

        if obj:
            inspect(obj[0], level + 1, max_level)


for filename in files:
    path = os.path.join(DATA_DIR, filename)

    print("\n" + "=" * 60)
    print(filename)
    print("=" * 60)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    inspect(data)