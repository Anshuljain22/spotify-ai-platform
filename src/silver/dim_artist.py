from pathlib import Path

import pandas as pd


BRONZE_ROOT = Path("data/bronze/saved_tracks")
SILVER_ROOT = Path("data/silver/dim_artist")


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

OUTPUT_FILE = OUTPUT_DIR / "dim_artist.parquet"


df = pd.read_parquet(BRONZE_FILE)


artists = df[
    ["artist_ids", "artist_names"]
].explode(
    ["artist_ids", "artist_names"]
)

artists = artists.rename(
    columns={
        "artist_ids": "artist_id",
        "artist_names": "artist_name"
    }
)

artists = artists.dropna(subset=["artist_id"])

artists = artists.drop_duplicates(
    subset=["artist_id"]
)

artists.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("SILVER DIM_ARTIST COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Input    : {BRONZE_FILE}")
print(f"Output   : {OUTPUT_FILE}")
print(f"Rows     : {len(artists)}")
print(f"Columns  : {len(artists.columns)}")
print()
print("Unique artist IDs:", artists["artist_id"].nunique())
print("Null artist IDs  :", artists["artist_id"].isna().sum())