from pathlib import Path

import pandas as pd


BRONZE_ROOT = Path("data/bronze/saved_tracks")
SILVER_ROOT = Path("data/silver/dim_track")


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

OUTPUT_FILE = OUTPUT_DIR / "dim_track.parquet"


df = pd.read_parquet(BRONZE_FILE)


tracks = df[
    [
        "track_id",
        "track_name",
        "album_id",
        "duration_ms",
        "disc_number",
        "track_number",
        "explicit",
        "is_local",
        "is_playable",
        "isrc",
        "track_uri",
        "track_url",
    ]
].copy()


tracks = tracks.dropna(subset=["track_id"])

tracks = tracks.drop_duplicates(
    subset=["track_id"]
)


tracks.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("SILVER DIM_TRACK COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Input    : {BRONZE_FILE}")
print(f"Output   : {OUTPUT_FILE}")
print(f"Rows     : {len(tracks)}")
print(f"Columns  : {len(tracks.columns)}")
print()
print("Unique track IDs:", tracks["track_id"].nunique())
print("Null track IDs  :", tracks["track_id"].isna().sum())