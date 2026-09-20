from pathlib import Path

import pandas as pd


BRONZE_ROOT = Path("data/bronze/saved_tracks")
SILVER_ROOT = Path("data/silver/track_artist")


snapshots = sorted(
    [p for p in BRONZE_ROOT.iterdir() if p.is_dir()],
    reverse=True
)

if not snapshots:
    raise FileNotFoundError("No Bronze snapshots found.")


SNAPSHOT_DIR = snapshots[0]
SNAPSHOT_ID = SNAPSHOT_DIR.name.replace("snapshot=", "")

BRONZE_FILE = SNAPSHOT_DIR / "saved_tracks.parquet"

OUTPUT_DIR = SILVER_ROOT / f"snapshot={SNAPSHOT_ID}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "track_artist.parquet"


df = pd.read_parquet(BRONZE_FILE)


track_artist = df[
    [
        "track_id",
        "artist_ids",
    ]
].copy()


track_artist = track_artist.explode(
    "artist_ids"
)


track_artist = track_artist.rename(
    columns={
        "artist_ids": "artist_id"
    }
)


track_artist = track_artist.dropna(
    subset=["track_id", "artist_id"]
)


track_artist = track_artist.drop_duplicates(
    subset=["track_id", "artist_id"]
)


track_artist.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("SILVER TRACK_ARTIST COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Input    : {BRONZE_FILE}")
print(f"Output   : {OUTPUT_FILE}")
print(f"Rows     : {len(track_artist)}")
print(f"Columns  : {len(track_artist.columns)}")
print()
print("Unique tracks :", track_artist["track_id"].nunique())
print("Unique artists:", track_artist["artist_id"].nunique())
print(
    "Duplicate relationships:",
    track_artist.duplicated(
        subset=["track_id", "artist_id"]
    ).sum()
)