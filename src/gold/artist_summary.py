from pathlib import Path

import pandas as pd


SILVER_ROOT = Path("data/silver")
GOLD_ROOT = Path("data/gold/artist_summary")


def latest_snapshot(table_name):
    table_root = SILVER_ROOT / table_name

    snapshots = sorted(
        [p for p in table_root.iterdir() if p.is_dir()],
        reverse=True
    )

    if not snapshots:
        raise FileNotFoundError(
            f"No Silver snapshots found for {table_name}"
        )

    snapshot_dir = snapshots[0]
    snapshot_id = snapshot_dir.name.replace("snapshot=", "")

    return snapshot_id, snapshot_dir


artist_snapshot, artist_dir = latest_snapshot("dim_artist")
track_snapshot, track_dir = latest_snapshot("dim_track")
relationship_snapshot, relationship_dir = latest_snapshot("track_artist")


if not (
    artist_snapshot == track_snapshot == relationship_snapshot
):
    raise ValueError(
        "Silver tables are from different snapshots."
    )


SNAPSHOT_ID = artist_snapshot


ARTIST_FILE = artist_dir / "dim_artist.parquet"
TRACK_FILE = track_dir / "dim_track.parquet"
RELATIONSHIP_FILE = relationship_dir / "track_artist.parquet"


artists = pd.read_parquet(ARTIST_FILE)
tracks = pd.read_parquet(TRACK_FILE)
track_artist = pd.read_parquet(RELATIONSHIP_FILE)


track_artist = track_artist.merge(
    tracks[
        [
            "track_id",
            "album_id",
        ]
    ],
    on="track_id",
    how="left"
)


artist_summary = track_artist.groupby(
    "artist_id"
).agg(
    saved_track_count=("track_id", "nunique"),
    album_count=("album_id", "nunique")
).reset_index()


artist_summary = artist_summary.merge(
    artists[
        [
            "artist_id",
            "artist_name",
        ]
    ],
    on="artist_id",
    how="left"
)


artist_summary = artist_summary[
    [
        "artist_id",
        "artist_name",
        "saved_track_count",
        "album_count",
    ]
]


artist_summary = artist_summary.sort_values(
    "saved_track_count",
    ascending=False
)


OUTPUT_DIR = GOLD_ROOT / f"snapshot={SNAPSHOT_ID}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "artist_summary.parquet"


artist_summary.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("GOLD ARTIST_SUMMARY COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Artists  : {len(artist_summary)}")
print(f"Output   : {OUTPUT_FILE}")
print()
print(artist_summary.head(10).to_string(index=False))