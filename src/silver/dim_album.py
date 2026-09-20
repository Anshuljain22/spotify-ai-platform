from pathlib import Path

import pandas as pd


BRONZE_ROOT = Path("data/bronze/saved_tracks")
SILVER_ROOT = Path("data/silver/dim_album")


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

OUTPUT_FILE = OUTPUT_DIR / "dim_album.parquet"


df = pd.read_parquet(BRONZE_FILE)


albums = df[
    [
        "album_id",
        "album_name",
        "album_type",
        "album_release_date",
    ]
].copy()


albums = albums.dropna(subset=["album_id"])

albums = albums.drop_duplicates(
    subset=["album_id"]
)


albums.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("SILVER DIM_ALBUM COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Input    : {BRONZE_FILE}")
print(f"Output   : {OUTPUT_FILE}")
print(f"Rows     : {len(albums)}")
print(f"Columns  : {len(albums.columns)}")
print()
print("Unique album IDs:", albums["album_id"].nunique())
print("Null album IDs  :", albums["album_id"].isna().sum())