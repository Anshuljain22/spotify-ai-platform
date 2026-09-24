from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def run_stage(name, command):
    print("\n" + "=" * 70)
    print(f"STAGE: {name}")
    print("=" * 70)

    start = time.time()

    result = subprocess.run(
        [sys.executable, *command],
        cwd=PROJECT_ROOT,
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\nFAILED: {name}")
        print(f"Exit code: {result.returncode}")
        print(f"Elapsed: {elapsed:.1f}s")
        return False

    print(f"\nPASSED: {name}")
    print(f"Elapsed: {elapsed:.1f}s")
    return True


def get_snapshots():
    snapshots = sorted(
        path.name
        for path in RAW_DIR.iterdir()
        if (
            path.is_dir()
            and len(path.name) == 16
            and (path / "saved_tracks.json").exists()
        )
    )

    if len(snapshots) < 2:
        return None, snapshots[-1] if snapshots else None

    return snapshots[-2], snapshots[-1]


def main():
    print("=" * 70)
    print("SPOTIFY DATA PIPELINE")
    print("=" * 70)
    print(f"Project: {PROJECT_ROOT}")
    print()

    pipeline_start = time.time()

    # ================================================================
    # STAGE 1: Spotify batch ingestion
    # ================================================================

    if not run_stage(
        "Spotify batch ingestion",
        ["-m", "src.spotify_client"],
    ):
        sys.exit(1)

    # Find previous and current snapshots after ingestion
    previous_snapshot, current_snapshot = get_snapshots()

    if current_snapshot is None:
        print("\nFAILED: No current snapshot found.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("SNAPSHOT STATE")
    print("=" * 70)
    print(f"Previous snapshot: {previous_snapshot}")
    print(f"Current snapshot : {current_snapshot}")

    # ================================================================
    # STAGE 2: Incremental detection
    # ================================================================

    if previous_snapshot is not None:
        if not run_stage(
            "Incremental batch detection",
            [
                "-m",
                "src.batch_incremental",
                previous_snapshot,
                current_snapshot,
            ],
        ):
            sys.exit(1)
    else:
        print("\nSKIPPED: Incremental batch detection")
        print("Reason: No previous snapshot exists yet.")

    # ================================================================
    # STAGE 3: Bronze
    # ================================================================

    if not run_stage(
        "Bronze saved tracks",
        ["-m", "src.bronze.saved_tracks"],
    ):
        sys.exit(1)

    # ================================================================
    # STAGES 4-8: Silver
    # ================================================================

    silver_stages = [
        (
            "Silver dim_artist",
            ["-m", "src.silver.dim_artist"],
        ),
        (
            "Silver dim_album",
            ["-m", "src.silver.dim_album"],
        ),
        (
            "Silver dim_track",
            ["-m", "src.silver.dim_track"],
        ),
        (
            "Silver track_artist",
            ["-m", "src.silver.track_artist"],
        ),
        (
            "Silver fact_saved_track",
            ["-m", "src.silver.fact_saved_track"],
        ),
    ]

    for name, command in silver_stages:
        if not run_stage(name, command):
            sys.exit(1)

    # ================================================================
    # STAGES 9-11: Gold
    # ================================================================

    gold_stages = [
        (
            "Gold artist summary",
            ["-m", "src.gold.artist_summary"],
        ),
        (
            "Gold album summary",
            ["-m", "src.gold.album_summary"],
        ),
        (
            "Gold saved track summary",
            ["-m", "src.gold.saved_track_summary"],
        ),
    ]

    for name, command in gold_stages:
        if not run_stage(name, command):
            sys.exit(1)

    # ================================================================
    # STAGE 12: PostgreSQL
    # ================================================================

    if not run_stage(
        "Load Gold analytics to PostgreSQL",
        ["-m", "src.postgres.load_gold"],
    ):
        sys.exit(1)

    # ================================================================
    # COMPLETE
    # ================================================================

    elapsed = time.time() - pipeline_start

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"Total elapsed time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()