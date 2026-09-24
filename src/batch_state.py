import json
from pathlib import Path


STATE_FILE = Path("data") / "batch_state.json"


def load_state():
    if not STATE_FILE.exists():
        return {}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_file = STATE_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    temp_file.replace(STATE_FILE)


def get_last_snapshot():
    state = load_state()
    return state.get("last_snapshot")


def update_last_snapshot(snapshot_id):
    state = load_state()

    state["last_snapshot"] = snapshot_id

    save_state(state)


if __name__ == "__main__":
    print("Last snapshot:", get_last_snapshot())