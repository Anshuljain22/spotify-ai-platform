
import json
from pathlib import Path

import pandas as pd

from src.quality_checks import validate_saved_tracks, print_quality_report


RAW_ROOT = Path("data/raw")
BRONZE_ROOT = Path("data/bronze/saved_tracks")


def load_snapshot(snapshot_dir):
    raw_file = snapshot_dir / "saved_tracks.json"

    if not raw_file.exists():
        raise FileNotFoundError(
            f"saved_tracks.json not found: {raw_file}"
        )

    with open(raw_file, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_rows(data):
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

            "artist_ids": [
                artist.get("id")
                for artist in artists
            ],

            "artist_names": [
                artist.get("name")
                for artist in artists
            ],
        })

    return rows


def get_snapshots():
    snapshots = sorted(
        [
            p
            for p in RAW_ROOT.iterdir()
            if p.is_dir()
        ],
        reverse=True
    )

    if not snapshots:
        raise FileNotFoundError(
            "No raw snapshots found."
        )

    return snapshots


def main():
    snapshots = get_snapshots()

    current_snapshot = snapshots[0]
    current_snapshot_id = current_snapshot.name

    current_data = load_snapshot(current_snapshot)

    current_rows = extract_rows(current_data)
    current_df = pd.DataFrame(current_rows)

    # --------------------------------------------------------
    # DATA QUALITY VALIDATION
    # --------------------------------------------------------

    quality_result = validate_saved_tracks(current_df)

    print()
    print(f"Snapshot     : {current_snapshot_id}")
    print(f"Source       : {current_snapshot / 'saved_tracks.json'}")
    print()

    print_quality_report(quality_result)

    if not quality_result["valid"]:
        raise RuntimeError(
            "Data quality validation failed. "
            "Bronze ingestion stopped."
        )

    # --------------------------------------------------------
    # FULL BRONZE SNAPSHOT
    # --------------------------------------------------------

    snapshot_output_dir = (
        BRONZE_ROOT /
        f"snapshot={current_snapshot_id}"
    )

    snapshot_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    snapshot_output_file = (
        snapshot_output_dir /
        "saved_tracks.parquet"
    )

    current_df.to_parquet(
        snapshot_output_file,
        engine="pyarrow",
        index=False
    )

    # --------------------------------------------------------
    # INCREMENTAL CHANGE DETECTION
    # --------------------------------------------------------

    previous_snapshot = (
        snapshots[1]
        if len(snapshots) > 1
        else None
    )

    incremental_df = current_df.iloc[0:0].copy()

    if previous_snapshot is not None:
        previous_data = load_snapshot(previous_snapshot)

        previous_rows = extract_rows(previous_data)
        previous_df = pd.DataFrame(previous_rows)

        previous_track_ids = set(
            previous_df["track_id"].dropna()
        )

        incremental_df = current_df[
            ~current_df["track_id"].isin(
                previous_track_ids
            )
        ].copy()

    # --------------------------------------------------------
    # INCREMENTAL BRONZE OUTPUT
    # --------------------------------------------------------

    incremental_output_dir = (
        BRONZE_ROOT /
        f"incremental={current_snapshot_id}"
    )

    incremental_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    incremental_output_file = (
        incremental_output_dir /
        "new_saved_tracks.parquet"
    )

    incremental_df.to_parquet(
        incremental_output_file,
        engine="pyarrow",
        index=False
    )

    # --------------------------------------------------------
    # FINAL INGESTION REPORT
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("BRONZE SNAPSHOT INGESTION COMPLETE")
    print("=" * 60)

    print(f"Snapshot       : {current_snapshot_id}")
    print(f"Full Output    : {snapshot_output_file}")
    print(f"Full Rows      : {len(current_df)}")

    print()
    print(
        f"Previous       : "
        f"{previous_snapshot.name if previous_snapshot else 'None'}"
    )
    print(f"Incremental    : {incremental_output_file}")
    print(f"New Rows       : {len(incremental_df)}")

    print()
    print(f"Columns        : {len(current_df.columns)}")


if __name__ == "__main__":
    main()

