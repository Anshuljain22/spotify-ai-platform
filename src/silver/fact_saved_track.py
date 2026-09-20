from pathlib import Path

import pandas as pd


BRONZE_ROOT = Path("data/bronze/saved_tracks")
SILVER_ROOT = Path("data/silver/fact_saved_track")


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

OUTPUT_FILE = OUTPUT_DIR / "fact_saved_track.parquet"


df = pd.read_parquet(BRONZE_FILE)


saved_tracks = df[
    [
        "track_id",
        "added_at",
    ]
].copy()


saved_tracks = saved_tracks.dropna(
    subset=["track_id", "added_at"]
)


saved_tracks["added_at"] = pd.to_datetime(
    saved_tracks["added_at"],
    utc=True
)


saved_tracks = saved_tracks.drop_duplicates(
    subset=["track_id", "added_at"]
)


saved_tracks.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("SILVER FACT_SAVED_TRACK COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Input    : {BRONZE_FILE}")
print(f"Output   : {OUTPUT_FILE}")
print(f"Rows     : {len(saved_tracks)}")
print(f"Columns  : {len(saved_tracks.columns)}")
print()
print(
    "Unique tracks:",
    saved_tracks["track_id"].nunique()
)
print(
    "Null track IDs:",
    saved_tracks["track_id"].isna().sum()
)
print(
    "Duplicate events:",
    saved_tracks.duplicated(
        subset=["track_id", "added_at"]
    ).sum()
)