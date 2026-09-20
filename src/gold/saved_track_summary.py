from pathlib import Path

import pandas as pd


SILVER_ROOT = Path("data/silver")
GOLD_ROOT = Path("data/gold/saved_track_summary")


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


track_snapshot, track_dir = latest_snapshot("dim_track")
album_snapshot, album_dir = latest_snapshot("dim_album")
artist_snapshot, artist_dir = latest_snapshot("dim_artist")
relationship_snapshot, relationship_dir = latest_snapshot("track_artist")
saved_snapshot, saved_dir = latest_snapshot("fact_saved_track")


snapshots = {
    track_snapshot,
    album_snapshot,
    artist_snapshot,
    relationship_snapshot,
    saved_snapshot,
}

if len(snapshots) != 1:
    raise ValueError(
        "Silver tables are from different snapshots."
    )


SNAPSHOT_ID = track_snapshot


TRACK_FILE = track_dir / "dim_track.parquet"
ALBUM_FILE = album_dir / "dim_album.parquet"
ARTIST_FILE = artist_dir / "dim_artist.parquet"
RELATIONSHIP_FILE = relationship_dir / "track_artist.parquet"
SAVED_FILE = saved_dir / "fact_saved_track.parquet"


tracks = pd.read_parquet(TRACK_FILE)
albums = pd.read_parquet(ALBUM_FILE)
artists = pd.read_parquet(ARTIST_FILE)
track_artist = pd.read_parquet(RELATIONSHIP_FILE)
saved_tracks = pd.read_parquet(SAVED_FILE)


summary = saved_tracks.merge(
    tracks,
    on="track_id",
    how="left"
)


summary = summary.merge(
    albums[
        [
            "album_id",
            "album_name",
            "album_type",
            "album_release_date",
        ]
    ],
    on="album_id",
    how="left"
)


artist_counts = track_artist.groupby(
    "track_id"
)["artist_id"].nunique().reset_index(
    name="artist_count"
)


summary = summary.merge(
    artist_counts,
    on="track_id",
    how="left"
)


summary = summary[
    [
        "track_id",
        "track_name",
        "album_id",
        "album_name",
        "album_type",
        "album_release_date",
        "duration_ms",
        "explicit",
        "isrc",
        "added_at",
        "artist_count",
    ]
]


summary = summary.sort_values(
    "added_at",
    ascending=False
)


OUTPUT_DIR = GOLD_ROOT / f"snapshot={SNAPSHOT_ID}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "saved_track_summary.parquet"


summary.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("GOLD SAVED_TRACK_SUMMARY COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Tracks   : {len(summary)}")
print(f"Output   : {OUTPUT_FILE}")
print()
print(summary.head(10).to_string(index=False))