import json
from pathlib import Path


RAW_DIR = Path("data") / "raw"


def load_saved_tracks(snapshot_id):
    file_path = RAW_DIR / snapshot_id / "saved_tracks.json"

    if not file_path.exists():
        raise FileNotFoundError(
            f"saved_tracks.json not found for snapshot {snapshot_id}"
        )

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("items", [])


def extract_track_ids(saved_tracks):
    track_ids = set()

    for item in saved_tracks:
        track = item.get("track")

        if not track:
            continue

        track_id = track.get("id")

        if track_id:
            track_ids.add(track_id)

    return track_ids


def compare_saved_tracks(previous_snapshot, current_snapshot):
    previous_data = load_saved_tracks(previous_snapshot)
    current_data = load_saved_tracks(current_snapshot)

    previous_ids = extract_track_ids(previous_data)
    current_ids = extract_track_ids(current_data)

    new_track_ids = current_ids - previous_ids
    removed_track_ids = previous_ids - current_ids

    return {
        "previous_snapshot": previous_snapshot,
        "current_snapshot": current_snapshot,
        "previous_count": len(previous_ids),
        "current_count": len(current_ids),
        "new_count": len(new_track_ids),
        "removed_count": len(removed_track_ids),
        "new_track_ids": sorted(new_track_ids),
        "removed_track_ids": sorted(removed_track_ids),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print(
            "Usage: python -m src.batch_incremental "
            "<previous_snapshot> <current_snapshot>"
        )
        raise SystemExit(1)

    previous_snapshot = sys.argv[1]
    current_snapshot = sys.argv[2]

    result = compare_saved_tracks(
        previous_snapshot,
        current_snapshot,
    )

    print(json.dumps(result, indent=2))