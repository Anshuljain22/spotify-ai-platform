import os
import json
from datetime import datetime, timezone

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

SCOPE = (
    "user-read-private "
    "user-read-email "
    "user-top-read "
    "user-read-recently-played "
    "user-library-read "
    "playlist-read-private "
    "playlist-read-collaborative "
    "user-follow-read "
    "user-read-currently-playing "
    "user-read-playback-state"
)

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=True
    )
)


# ============================================================
# SNAPSHOT DIRECTORY
# ============================================================

run_time = datetime.now(timezone.utc)

snapshot_id = run_time.strftime("%Y%m%dT%H%M%SZ")

snapshot_dir = os.path.join(
    "data",
    "raw",
    snapshot_id
)

os.makedirs(snapshot_dir, exist_ok=True)


# ============================================================
# HELPER
# ============================================================

def save_json(filename, data):
    path = os.path.join(snapshot_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved: {path}")


def collect_paginated(fetch_function, limit=50):
    """
    Collect all pages from a Spotify endpoint that supports
    limit/offset pagination.
    """

    results = []
    offset = 0

    while True:

        response = fetch_function(
            limit=limit,
            offset=offset
        )

        items = response.get("items", [])

        results.extend(items)

        total = response.get("total")

        print(
            f"Fetched {len(items)} items "
            f"(total collected: {len(results)}"
            + (f" / {total})" if total is not None else ")")
        )

        if not items:
            break

        if total is not None and len(results) >= total:
            break

        if len(items) < limit:
            break

        offset += limit

    return results


# ============================================================
# PROFILE
# ============================================================

print("\n" + "=" * 60)
print("PROFILE")
print("=" * 60)

profile = sp.current_user()

save_json("profile.json", profile)

print("User:", profile.get("display_name"))
print("ID:", profile.get("id"))


# ============================================================
# SAVED / LIKED TRACKS
# ============================================================

print("\n" + "=" * 60)
print("SAVED TRACKS")
print("=" * 60)

saved_tracks = collect_paginated(
    sp.current_user_saved_tracks,
    limit=50
)

save_json(
    "saved_tracks.json",
    {
        "collected_at": run_time.isoformat(),
        "count": len(saved_tracks),
        "items": saved_tracks
    }
)

print("Total saved tracks:", len(saved_tracks))


# ============================================================
# PLAYLISTS
# ============================================================

print("\n" + "=" * 60)
print("PLAYLISTS")
print("=" * 60)

playlists = collect_paginated(
    sp.current_user_playlists,
    limit=50
)

save_json(
    "playlists.json",
    {
        "collected_at": run_time.isoformat(),
        "count": len(playlists),
        "items": playlists
    }
)

print("Total playlists:", len(playlists))


# ============================================================
# PLAYLIST ITEMS
# ============================================================

print("\n" + "=" * 60)
print("PLAYLIST ITEMS")
print("=" * 60)

playlist_items = []

for index, playlist in enumerate(playlists, 1):

    playlist_id = playlist.get("id")
    playlist_name = playlist.get("name")

    print(
        f"\n[{index}/{len(playlists)}] "
        f"{playlist_name}"
    )

    if not playlist_id:
        continue

    try:

        items = collect_paginated(
            lambda limit, offset:
                sp.playlist_items(
                    playlist_id,
                    limit=limit,
                    offset=offset
                ),
            limit=50
        )

        for item in items:

            playlist_items.append({
                "playlist_id": playlist_id,
                "playlist_name": playlist_name,
                "item": item
            })

    except Exception as e:

        print(
            f"Could not read playlist "
            f"{playlist_name}: {e}"
        )


save_json(
    "playlist_items.json",
    {
        "collected_at": run_time.isoformat(),
        "count": len(playlist_items),
        "items": playlist_items
    }
)

print(
    "Total playlist items:",
    len(playlist_items)
)


# ============================================================
# FOLLOWED ARTISTS
# ============================================================

print("\n" + "=" * 60)
print("FOLLOWED ARTISTS")
print("=" * 60)

try:

    followed_artists = sp.current_user_followed_artists(
        limit=50
    )

    save_json(
        "followed_artists.json",
        followed_artists
    )

    artists = followed_artists.get(
        "artists",
        {}
    ).get(
        "items",
        []
    )

    print(
        "Followed artists:",
        len(artists)
    )

except Exception as e:

    print("Could not collect followed artists:", e)


# ============================================================
# TOP ARTISTS
# ============================================================

print("\n" + "=" * 60)
print("TOP ARTISTS")
print("=" * 60)

top_artists = {}

for time_range in [
    "short_term",
    "medium_term",
    "long_term"
]:

    try:

        response = sp.current_user_top_artists(
            limit=50,
            time_range=time_range
        )

        top_artists[time_range] = response

        print(
            time_range,
            ":",
            len(response.get("items", []))
        )

    except Exception as e:

        print(
            f"Could not collect "
            f"{time_range} top artists:",
            e
        )


save_json(
    "top_artists.json",
    top_artists
)


# ============================================================
# TOP TRACKS
# ============================================================

print("\n" + "=" * 60)
print("TOP TRACKS")
print("=" * 60)

top_tracks = {}

for time_range in [
    "short_term",
    "medium_term",
    "long_term"
]:

    try:

        response = sp.current_user_top_tracks(
            limit=50,
            time_range=time_range
        )

        top_tracks[time_range] = response

        print(
            time_range,
            ":",
            len(response.get("items", []))
        )

    except Exception as e:

        print(
            f"Could not collect "
            f"{time_range} top tracks:",
            e
        )


save_json(
    "top_tracks.json",
    top_tracks
)


# ============================================================
# RECENTLY PLAYED
# ============================================================

print("\n" + "=" * 60)
print("RECENTLY PLAYED")
print("=" * 60)

try:

    recently_played = sp.current_user_recently_played(
        limit=50
    )

    save_json(
        "recently_played.json",
        recently_played
    )

    print(
        "Recently played:",
        len(recently_played.get("items", []))
    )

except Exception as e:

    print(
        "Could not collect recently played:",
        e
    )


# ============================================================
# RUN METADATA
# ============================================================

metadata = {
    "snapshot_id": snapshot_id,
    "collected_at": run_time.isoformat(),
    "collector_version": "1.0",
    "datasets": [
        "profile",
        "saved_tracks",
        "playlists",
        "playlist_items",
        "followed_artists",
        "top_artists",
        "top_tracks",
        "recently_played"
    ]
}

save_json(
    "_metadata.json",
    metadata
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 60)
print("COLLECTION COMPLETE")
print("=" * 60)

print("Snapshot:", snapshot_id)
print("Location:", snapshot_dir)