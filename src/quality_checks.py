
import pandas as pd


REQUIRED_COLUMNS = [
    "added_at",
    "track_id",
    "track_name",
    "duration_ms",
    "explicit",
    "album_id",
    "album_name",
    "artist_ids",
    "artist_names",
]


def validate_saved_tracks(df):
    errors = []
    warnings = []

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(
            f"Missing required columns: {missing_columns}"
        )

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "row_count": len(df),
        }

    # --------------------------------------------------------
    # EMPTY DATASET
    # --------------------------------------------------------

    if len(df) == 0:
        errors.append("Dataset is empty.")

    # --------------------------------------------------------
    # NULL CHECKS
    # --------------------------------------------------------

    null_track_ids = df["track_id"].isna().sum()

    if null_track_ids > 0:
        errors.append(
            f"Found {null_track_ids} rows with missing track_id."
        )

    null_track_names = df["track_name"].isna().sum()

    if null_track_names > 0:
        errors.append(
            f"Found {null_track_names} rows with missing track_name."
        )

    null_added_at = df["added_at"].isna().sum()

    if null_added_at > 0:
        errors.append(
            f"Found {null_added_at} rows with missing added_at."
        )

    # --------------------------------------------------------
    # DUPLICATE CHECK
    # --------------------------------------------------------

    duplicate_track_ids = (
        df["track_id"]
        .dropna()
        .duplicated()
        .sum()
    )

    if duplicate_track_ids > 0:
        errors.append(
            f"Found {duplicate_track_ids} duplicate track_id values."
        )

    # --------------------------------------------------------
    # INVALID VALUES
    # --------------------------------------------------------

    invalid_duration = (
        df["duration_ms"].notna()
        & (df["duration_ms"] <= 0)
    ).sum()

    if invalid_duration > 0:
        errors.append(
            f"Found {invalid_duration} tracks with invalid duration_ms."
        )

    # --------------------------------------------------------
    # ARTIST DATA
    # --------------------------------------------------------

    missing_artist_data = (
        df["artist_ids"].apply(
            lambda value: not isinstance(value, list)
            or len(value) == 0
        )
    ).sum()

    if missing_artist_data > 0:
        warnings.append(
            f"Found {missing_artist_data} rows without artist information."
        )

    # --------------------------------------------------------
    # WARNING: SMALL DATASET
    # --------------------------------------------------------

    if len(df) < 10:
        warnings.append(
            f"Dataset contains only {len(df)} rows."
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
    }


def print_quality_report(result):
    print("=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)

    print(f"Status       : {'PASS' if result['valid'] else 'FAIL'}")
    print(f"Rows         : {result['row_count']}")

    print()

    if result["errors"]:
        print("ERRORS:")
        for error in result["errors"]:
            print(f"  - {error}")
    else:
        print("Errors       : None")

    print()

    if result["warnings"]:
        print("WARNINGS:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    else:
        print("Warnings     : None")

    print("=" * 60)


if __name__ == "__main__":
    from pathlib import Path
    import json

    raw_root = Path("data/raw")

    snapshots = sorted(
        [
            p
            for p in raw_root.iterdir()
            if p.is_dir()
        ],
        reverse=True
    )

    if not snapshots:
        raise FileNotFoundError(
            "No raw snapshots found."
        )

    latest_snapshot = snapshots[0]

    raw_file = latest_snapshot / "saved_tracks.json"

    with open(raw_file, "r", encoding="utf-8") as f:
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
            "explicit": track.get("explicit"),
            "album_id": album.get("id"),
            "album_name": album.get("name"),
            "artist_ids": [
                artist.get("id")
                for artist in artists
            ],
            "artist_names": [
                artist.get("name")
                for artist in artists
            ],
        })

    df = pd.DataFrame(rows)

    result = validate_saved_tracks(df)

    print(f"Snapshot     : {latest_snapshot.name}")
    print(f"Source       : {raw_file}")
    print()

    print_quality_report(result)

    if not result["valid"]:
        raise SystemExit(1)

