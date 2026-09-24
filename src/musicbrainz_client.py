import requests
import time
from urllib.parse import quote


BASE_URL = "https://musicbrainz.org/ws/2"

HEADERS = {
    "User-Agent": "SpotifyAIPlatform/1.0 (spotify-ai-platform@example.com)"
}


def search_artist(artist_name):
    url = f"{BASE_URL}/artist/"

    params = {
        "query": f'artist:"{artist_name}"',
        "fmt": "json",
        "limit": 1,
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    artists = data.get("artists", [])

    if not artists:
        return None

    artist = artists[0]

    time.sleep(1.0)

    return {
        "mbid": artist.get("id"),
        "name": artist.get("name"),
        "country": artist.get("country"),
        "disambiguation": artist.get("disambiguation"),
        "type": artist.get("type"),
        "score": artist.get("score"),
    }


def get_artist(artist_mbid):
    url = f"{BASE_URL}/artist/{quote(artist_mbid)}"

    params = {
        "fmt": "json",
        "inc": "genres+tags",
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    return {
        "mbid": data.get("id"),
        "name": data.get("name"),
        "country": data.get("country"),
        "type": data.get("type"),
        "disambiguation": data.get("disambiguation"),
        "genres": [
            genre.get("name")
            for genre in data.get("genres", [])
        ],
        "tags": [
            tag.get("name")
            for tag in data.get("tags", [])
        ],
    }


def get_artist_info(artist_name):
    artist = search_artist(artist_name)

    if not artist:
        return {
            "artist": artist_name,
            "found": False,
        }

    details = get_artist(artist["mbid"])

    return {
        "found": True,
        **details,
    }


if __name__ == "__main__":
    result = get_artist_info("Metro Boomin")

    print(result)