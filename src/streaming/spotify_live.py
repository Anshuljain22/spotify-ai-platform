import json
import time
from datetime import datetime, timezone

from kafka import KafkaProducer

from src.spotify_client import sp


KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"
KAFKA_TOPIC = "spotify-listening"
POLL_INTERVAL = 10


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    key_serializer=lambda key: key.encode("utf-8"),
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)


def get_currently_playing():
    try:
        playback = sp.current_playback()

        if not playback:
            return None

        track = playback.get("item")

        if not track:
            return None

        return {
            "event_type": "now_playing",
            "track_id": track.get("id"),
            "track_name": track.get("name"),
            "artist_ids": [
                artist.get("id")
                for artist in track.get("artists", [])
            ],
            "artist_names": [
                artist.get("name")
                for artist in track.get("artists", [])
            ],
            "album_id": track.get("album", {}).get("id"),
            "album_name": track.get("album", {}).get("name"),
            "is_playing": playback.get("is_playing"),
            "progress_ms": playback.get("progress_ms"),
            "duration_ms": track.get("duration_ms"),
            "spotify_timestamp": playback.get("timestamp"),
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        print(f"Spotify error: {e}")
        return None


def send_to_kafka(event):
    future = producer.send(
        KAFKA_TOPIC,
        key=event["track_id"],
        value=event
    )

    metadata = future.get(timeout=10)

    print(
        f"Kafka → topic={metadata.topic}, "
        f"partition={metadata.partition}, "
        f"offset={metadata.offset}"
    )


def print_event(event):
    print("\n" + "=" * 60)
    print("NOW PLAYING")
    print("=" * 60)

    print("Track:", event["track_name"])
    print("Artist:", ", ".join(event["artist_names"]))
    print("Album:", event["album_name"])
    print("Playing:", event["is_playing"])

    progress = event["progress_ms"] or 0
    duration = event["duration_ms"] or 0

    print(
        f"Progress: "
        f"{progress // 60000}:{(progress // 1000) % 60:02d}"
        f" / "
        f"{duration // 60000}:{(duration // 1000) % 60:02d}"
    )

    print("Collected:", event["collected_at"])


def main():
    print("Starting Spotify → Kafka live listener...")
    print(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic: {KAFKA_TOPIC}")
    print(f"Polling every {POLL_INTERVAL} seconds.")
    print("Press Ctrl+C to stop.\n")

    last_track_id = None

    try:
        while True:

            event = get_currently_playing()

            if event:

                track_id = event["track_id"]

                if track_id != last_track_id:

                    print_event(event)

                    send_to_kafka(event)

                    last_track_id = track_id

            else:

                if last_track_id is not None:
                    print("\nNothing is currently playing.")

                last_track_id = None

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:

        print("\nStopping Spotify → Kafka listener...")

    finally:

        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()