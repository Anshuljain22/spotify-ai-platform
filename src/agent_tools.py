import json
from pathlib import Path

import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.musicbrainz_client import get_artist_info


SPARK_WAREHOUSE = "data/iceberg"

_spark = None


def get_spark():
    """Return the shared Spark session used by the analytics tools."""
    global _spark

    if _spark is None:
        _spark = (
            SparkSession.builder
            .appName("SpotifyAgentTools")
            .config(
                "spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-4.1_2.13:1.11.0",
            )
            .config(
                "spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            )
            .config(
                "spark.sql.catalog.local",
                "org.apache.iceberg.spark.SparkCatalog",
            )
            .config(
                "spark.sql.catalog.local.type",
                "hadoop",
            )
            .config(
                "spark.sql.catalog.local.warehouse",
                "data/iceberg",
            )
            .config(
                "spark.sql.streaming.metricsEnabled",
                "false",
            )
            .getOrCreate()
        )

        _spark.sparkContext.setLogLevel("WARN")

    return _spark


def get_postgres_connection():
    """Create a connection to the Spotify PostgreSQL analytics database."""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="spotify_analytics",
        user="postgres",
        password="postgres",
    )


def query_track_analytics(track_name: str):
    """Query listening analytics for a specific track."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_analytics")

    result = (
        df.filter(
            F.lower(F.col("track_name")).contains(track_name.lower())
        )
        .orderBy(F.desc("play_events"))
        .limit(10)
        .collect()
    )

    return [
        {
            "track_id": row["track_id"],
            "track_name": row["track_name"],
            "artists": row["artists"],
            "play_events": row["play_events"],
            "avg_progress_pct": row["avg_progress_pct"],
            "latest_played_at": str(row["latest_played_at"]),
        }
        for row in result
    ]


def query_artist_analytics(artist_name: str):
    """Query listening analytics for a specific artist."""

    spark = get_spark()

    df = spark.table("local.spotify.artist_listening_analytics")

    result = (
        df.filter(
            F.lower(F.col("artist")).contains(artist_name.lower())
        )
        .orderBy(F.desc("play_events"))
        .limit(10)
        .collect()
    )

    return [
        {
            "artist": row["artist"],
            "play_events": row["play_events"],
            "unique_tracks": row["unique_tracks"],
            "avg_completion_pct": row["avg_completion_pct"],
            "latest_listening_at": str(row["latest_listening_at"]),
        }
        for row in result
    ]


def query_recent_listening(limit: int = 10):
    """Return the most recent listening events."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_events")

    result = (
        df.filter(F.col("is_playing") == True)
        .orderBy(F.desc("collected_at_ts"))
        .limit(limit)
        .collect()
    )

    return [
        {
            "track_name": row["track_name"],
            "artists": row["artist_names"],
            "album_name": row["album_name"],
            "progress_pct": row["progress_pct"],
            "collected_at": str(row["collected_at_ts"]),
        }
        for row in result
    ]


def query_saved_tracks(limit: int = 20):
    """Return saved tracks from the Spotify PostgreSQL analytics database."""

    conn = get_postgres_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                track_id,
                track_name,
                album_name,
                album_type,
                album_release_date,
                duration_ms,
                explicit,
                isrc,
                added_at,
                artist_count
            FROM saved_track_summary
            ORDER BY added_at DESC
            LIMIT %s
            """,
            (limit,),
        )

        rows = cursor.fetchall()

        return [
            {
                "track_id": row[0],
                "track_name": row[1],
                "album_name": row[2],
                "album_type": row[3],
                "album_release_date": row[4],
                "duration_ms": row[5],
                "explicit": row[6],
                "isrc": row[7],
                "added_at": str(row[8]),
                "artist_count": row[9],
            }
            for row in rows
        ]

    finally:
        conn.close()


def get_currently_playing():
    """Return the track currently playing on Spotify."""

    from src.spotify_client import sp

    current = sp.current_user_playing_track()

    if not current or not current.get("item"):
        return {
            "is_playing": False,
            "message": "Nothing is currently playing.",
        }

    track = current["item"]

    return {
        "is_playing": current.get("is_playing", False),
        "track_name": track.get("name"),
        "artists": [
            artist.get("name")
            for artist in track.get("artists", [])
        ],
        "album_name": track.get("album", {}).get("name"),
        "progress_ms": current.get("progress_ms"),
        "duration_ms": track.get("duration_ms"),
    }


def query_listening_trends(limit: int = 10):
    """Return tracks ordered by observed listening activity."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_analytics")

    result = (
        df.orderBy(F.desc("play_events"))
        .limit(limit)
        .collect()
    )

    return [
        {
            "track_id": row["track_id"],
            "track_name": row["track_name"],
            "artists": row["artists"],
            "play_events": row["play_events"],
            "avg_progress_pct": row["avg_progress_pct"],
            "latest_played_at": str(row["latest_played_at"]),
        }
        for row in result
    ]


def query_listening_window(days: int = 7):
    """Return listening events observed within the requested number of days."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_events")

    cutoff = F.current_timestamp() - F.expr(
        f"INTERVAL {int(days)} DAYS"
    )

    result = (
        df.filter(
            (F.col("is_playing") == True)
            & (F.col("collected_at_ts") >= cutoff)
        )
        .orderBy(F.desc("collected_at_ts"))
        .collect()
    )

    return [
        {
            "track_name": row["track_name"],
            "artists": row["artist_names"],
            "album_name": row["album_name"],
            "progress_pct": row["progress_pct"],
            "collected_at": str(row["collected_at_ts"]),
        }
        for row in result
    ]


def query_listening_summary(days: int = 7):
    """Summarize observed listening activity over the requested time window."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_events")

    cutoff = F.current_timestamp() - F.expr(
        f"INTERVAL {int(days)} DAYS"
    )

    filtered = df.filter(
        (F.col("is_playing") == True)
        & (F.col("collected_at_ts") >= cutoff)
    )

    row = (
        filtered.agg(
            F.count("*").alias("play_events"),
            F.countDistinct("track_id").alias("unique_tracks"),
            F.avg("progress_pct").alias("avg_completion_pct"),
            F.max("collected_at_ts").alias("latest_listening_at"),
        )
        .collect()[0]
    )

    return {
        "days": days,
        "play_events": row["play_events"],
        "unique_tracks": row["unique_tracks"],
        "avg_completion_pct": row["avg_completion_pct"],
        "latest_listening_at": str(row["latest_listening_at"]),
    }


def query_saved_vs_listened(days: int = 7):
    """Compare saved tracks with tracks observed in recent listening events."""

    conn = get_postgres_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT track_id) FROM saved_track_summary")
        saved_count = cursor.fetchone()[0]
    finally:
        conn.close()

    spark = get_spark()

    listening = (
        spark.table("local.spotify.listening_events")
        .filter(
            (F.col("is_playing") == True)
            & (
                F.col("collected_at_ts")
                >= F.current_timestamp()
                - F.expr(f"INTERVAL {int(days)} DAYS")
            )
        )
        .select("track_id")
        .dropDuplicates()
    )

    listened_count = listening.count()

    listened_ids = [row["track_id"] for row in listening.collect()]

    if not listened_ids:
        overlap = 0
    else:
        conn = get_postgres_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(DISTINCT track_id)
                FROM saved_track_summary
                WHERE track_id = ANY(%s)
                """,
                (listened_ids,),
            )
            overlap = cursor.fetchone()[0]
        finally:
            conn.close()

    return {
        "days": days,
        "saved_tracks": saved_count,
        "recently_listened_unique_tracks": listened_count,
        "saved_and_listened_tracks": overlap,
    }


def query_listening_profile(days: int = 7):
    """Build a high-level profile of recent observed listening behavior."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_events")

    filtered = df.filter(
        (F.col("is_playing") == True)
        & (
            F.col("collected_at_ts")
            >= F.current_timestamp()
            - F.expr(f"INTERVAL {int(days)} DAYS")
        )
    )

    total_events = filtered.count()

    if total_events == 0:
        return {
            "days": days,
            "total_events": 0,
            "unique_tracks": 0,
            "unique_artists": 0,
            "average_completion_pct": None,
        }

    unique_tracks = filtered.select("track_id").distinct().count()

    unique_artists = (
        filtered
        .select(F.explode("artist_names").alias("artist"))
        .select("artist")
        .distinct()
        .count()
    )

    row = (
        filtered
        .agg(
            F.avg("progress_pct").alias("average_completion_pct")
        )
        .collect()[0]
    )

    return {
        "days": days,
        "total_events": total_events,
        "unique_tracks": unique_tracks,
        "unique_artists": unique_artists,
        "average_completion_pct": row["average_completion_pct"],
    }


def query_listening_patterns():
    """Return observed listening patterns across tracks and artists."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_events")

    filtered = df.filter(F.col("is_playing") == True)

    artist_counts = (
        filtered
        .select(F.explode("artist_names").alias("artist"))
        .groupBy("artist")
        .count()
        .orderBy(F.desc("count"))
        .limit(10)
        .collect()
    )

    track_counts = (
        filtered
        .groupBy("track_name")
        .count()
        .orderBy(F.desc("count"))
        .limit(10)
        .collect()
    )

    return {
        "top_artists": [
            {
                "artist": row["artist"],
                "play_events": row["count"],
            }
            for row in artist_counts
        ],
        "top_tracks": [
            {
                "track_name": row["track_name"],
                "play_events": row["count"],
            }
            for row in track_counts
        ],
    }


def query_artist_concentration():
    """Return concentration metrics for observed listening across artists."""

    spark = get_spark()

    df = spark.table("local.spotify.listening_concentration")

    row = df.limit(1).collect()

    if not row:
        return {
            "message": "No listening concentration data is available."
        }

    row = row[0]

    return {
        "total_artist_associations": row["total_events"],
        "top_artist": row["top_artist"],
        "top_artist_associations": row["top_artist_events"],
        "top_artist_association_share_pct": row["top_artist_association_share_pct"],
        "top_3_artist_association_share_pct": row["top_3_artist_association_share_pct"],
        "top_5_artist_association_share_pct": row["top_5_artist_association_share_pct"],
    }

def query_completion_behavior():
    """Return observed completion statistics and high- and low-completion tracks."""

    spark = get_spark()

    df = (
        spark.table("local.spotify.listening_events")
        .filter(F.col("is_playing") == True)
    )

    total_events = df.count()

    if total_events == 0:
        return {
            "total_events": 0,
            "average_completion_pct": None,
            "high_completion_events": 0,
            "low_completion_events": 0,
            "top_completed_tracks": [],
            "low_completion_tracks": [],
        }

    average_completion = (
        df.agg(
            F.avg("progress_pct").alias("average_completion_pct")
        )
        .collect()[0]["average_completion_pct"]
    )

    high_completion_events = df.filter(
        F.col("progress_pct") >= 80
    ).count()

    low_completion_events = df.filter(
        F.col("progress_pct") < 20
    ).count()

    track_stats = (
        df.groupBy(
            "track_name",
            "artist_names",
        )
        .agg(
            F.count("*").alias("observed_events"),
            F.avg("progress_pct").alias("avg_completion_pct"),
        )
    )

    top_completed = (
        track_stats
        .orderBy(F.desc("avg_completion_pct"))
        .limit(10)
        .collect()
    )

    low_completed = (
        track_stats
        .orderBy(F.asc("avg_completion_pct"))
        .limit(10)
        .collect()
    )

    return {
        "total_events": total_events,
        "average_completion_pct": average_completion,
        "high_completion_events": high_completion_events,
        "low_completion_events": low_completion_events,
        "top_completed_tracks": [
            {
                "track_name": row["track_name"],
                "artists": row["artist_names"],
                "observed_events": row["observed_events"],
                "avg_completion_pct": row["avg_completion_pct"],
            }
            for row in top_completed
        ],
        "low_completion_tracks": [
            {
                "track_name": row["track_name"],
                "artists": row["artist_names"],
                "observed_events": row["observed_events"],
                "avg_completion_pct": row["avg_completion_pct"],
            }
            for row in low_completed
        ],
    }


def get_artist_metadata(artist_name: str):
    """Retrieve external artist metadata from MusicBrainz."""

    return get_artist_info(artist_name)


if __name__ == "__main__":
    print(
        json.dumps(
            query_artist_concentration(),
            indent=2,
            default=str,
        )
    )