import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

STAGES = [
    ("Listening analytics", "src.analytics.build_listening_analytics"),
    ("Artist listening analytics", "src.analytics.build_artist_listening"),
    ("Daily listening analytics", "src.analytics.build_daily_listening"),
    ("Listening concentration", "src.analytics.build_listening_concentration"),
]

def main():
    print("=" * 70)
    print("SPOTIFY LISTENING ANALYTICS PIPELINE")
    print("=" * 70)

    for name, module in STAGES:
        print("\n" + "=" * 70)
        print(f"STAGE: {name}")
        print("=" * 70)

        result = subprocess.run(
            [sys.executable, "-m", module],
            cwd=PROJECT_ROOT,
        )

        if result.returncode != 0:
            print(f"\nFAILED: {name}")
            sys.exit(1)

        print(f"\nPASSED: {name}")

    print("\n" + "=" * 70)
    print("ANALYTICS PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    main()