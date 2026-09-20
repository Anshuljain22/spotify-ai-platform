from pathlib import Path

import pandas as pd


SILVER_ROOT = Path("data/silver")
GOLD_ROOT = Path("data/gold/album_summary")


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


album_snapshot, album_dir = latest_snapshot("dim_album")
track_snapshot, track_dir = latest_snapshot("dim_track")
relationship_snapshot, relationship_dir = latest_snapshot("track_artist")


if not (
    album_snapshot == track_snapshot == relationship_snapshot
):
    raise ValueError(
        "Silver tables are from different snapshots."
    )


SNAPSHOT_ID = album_snapshot


ALBUM_FILE = album_dir / "dim_album.parquet"
TRACK_FILE = track_dir / "dim_track.parquet"
RELATIONSHIP_FILE = relationship_dir / "track_artist.parquet"


albums = pd.read_parquet(ALBUM_FILE)
tracks = pd.read_parquet(TRACK_FILE)
track_artist = pd.read_parquet(RELATIONSHIP_FILE)


album_tracks = tracks[
    [
        "track_id",
        "album_id",
    ]
].dropna(subset=["album_id"])


track_artists = track_artist[
    [
        "track_id",
        "artist_id",
    ]
]


album_tracks = album_tracks.merge(
    track_artists,
    on="track_id",
    how="left"
)


album_summary = album_tracks.groupby(
    "album_id"
).agg(
    track_count=("track_id", "nunique"),
    artist_count=("artist_id", "nunique")
).reset_index()


album_summary = album_summary.merge(
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


album_summary = album_summary[
    [
        "album_id",
        "album_name",
        "album_type",
        "album_release_date",
        "track_count",
        "artist_count",
    ]
]


album_summary = album_summary.sort_values(
    "track_count",
    ascending=False
)


OUTPUT_DIR = GOLD_ROOT / f"snapshot={SNAPSHOT_ID}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "album_summary.parquet"


album_summary.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    index=False
)


print("=" * 60)
print("GOLD ALBUM_SUMMARY COMPLETE")
print("=" * 60)
print(f"Snapshot : {SNAPSHOT_ID}")
print(f"Albums   : {len(album_summary)}")
print(f"Output   : {OUTPUT_FILE}")
print()
print(album_summary.head(10).to_string(index=False))