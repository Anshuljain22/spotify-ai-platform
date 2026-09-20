import json
from pathlib import Path

import pandas as pd


RAW_ROOT = Path("data/raw")
BRONZE_ROOT = Path("data/bronze/saved_tracks")


snapshots = sorted(
    [p for p in RAW_ROOT.iterdir() if p.is_dir()],
    reverse=True
)

if not snapshots:
    raise FileNotFoundError("No raw snapshots found.")


SNAPSHOT_DIR = snapshots[0]
SNAPSHOT_ID = SNAPSHOT_DIR.name

RAW_FILE = SNAPSHOT_DIR / "saved_tracks.json"

OUTPUT_DIR = BRONZE_ROOT / f"snapshot={SNAPSHOT_ID}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "saved_tracks.parquet"


with open(RAW_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


rows = []

for item in data["items"]:
    track = item["track"]
    album = track.get("album", {})
    artists = track.get("artists", [])

    rows.append({
        "added_at": item.get("added_at"),

        "track_id": track.get("id"),
        "track_name": track.get("name"),
        "duration_ms": track.get("duration_ms"),
        "disc_number": track.get("disc_number"),
        "track_number": track.get("track_number"),
        "explicit": track.get("explicit"),
        "is_local": track.get("is_local"),
        "is_playable": track.get("is_playable"),
        "isrc": track.get("external_ids", {}).get("isrc"),
        "track_uri": track.get("uri"),
        "track_url": track.get("external_urls", {}).get("spotify"),

        "album_id": album.get("id"),
        "album_name": album.get("name"),
        "album_type": album.get("album_type"),
        "album_release_date": album.get("release_date"),

        "artist_ids": [artist.get("id") for artist in artists],
        "artist_names": [artist.get("name") for artist in artists],
    })


df = pd.DataFrame(rows)

df.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("BRONZE SNAPSHOT INGESTION COMPLETE")
print("=" * 60)
print(f"Snapshot: {SNAPSHOT_ID}")
print(f"Source  : {RAW_FILE}")
print(f"Output  : {OUTPUT_FILE}")
print(f"Rows    : {len(df)}")
print(f"Columns : {len(df.columns)}")