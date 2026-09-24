from pyspark.sql import SparkSession
from pyspark.sql import functions as F


WAREHOUSE = "data/iceberg"

ICEBERG_PACKAGE = (
    "org.apache.iceberg:"
    "iceberg-spark-runtime-4.1_2.13:"
    "1.11.0"
)


def get_spark():
    return (
        SparkSession.builder
        .appName("SpotifyArtistListeningAnalytics")
        .config("spark.jars.packages", ICEBERG_PACKAGE)
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
        )
        .config(
            "spark.sql.catalog.local",
            "org.apache.iceberg.spark.SparkCatalog"
        )
        .config(
            "spark.sql.catalog.local.type",
            "hadoop"
        )
        .config(
            "spark.sql.catalog.local.warehouse",
            WAREHOUSE
        )
        .getOrCreate()
    )


def main():
    spark = get_spark()

    spark.conf.set(
        "spark.sql.streaming.metricsEnabled",
        "false"
    )

    print("=" * 60)
    print("BUILDING ARTIST LISTENING ANALYTICS")
    print("=" * 60)

    df = spark.sql("""
        SELECT
            collected_at_ts,
            track_id,
            track_name,
            artist_names,
            progress_pct
        FROM local.spotify.listening_events
        WHERE is_playing = true
          AND collected_at_ts IS NOT NULL
          AND track_id IS NOT NULL
          AND artist_names IS NOT NULL
    """)

    artist_df = (
        df
        .withColumn(
            "artist",
            F.explode("artist_names")
        )
    )

    artist_summary = (
        artist_df
        .groupBy("artist")
        .agg(
            F.count("*").alias("play_events"),
            F.countDistinct("track_id").alias("unique_tracks"),
            F.round(
                F.avg("progress_pct"),
                2
            ).alias("avg_completion_pct"),
            F.max("collected_at_ts").alias(
                "latest_listening_at"
            )
        )
        .orderBy(F.desc("play_events"))
    )

    artist_summary.writeTo(
        "local.spotify.artist_listening_analytics"
    ).createOrReplace()

    print()
    print("TABLE:")
    print("local.spotify.artist_listening_analytics")

    print()
    print("SCHEMA:")
    spark.sql("""
        DESCRIBE local.spotify.artist_listening_analytics
    """).show(truncate=False)

    print()
    print("TOP ARTISTS:")

    spark.sql("""
        SELECT
            artist,
            play_events,
            unique_tracks,
            avg_completion_pct,
            latest_listening_at
        FROM local.spotify.artist_listening_analytics
        ORDER BY play_events DESC
        LIMIT 10
    """).show(10, truncate=False)

    print()
    print(
        "Artists:",
        spark.sql("""
            SELECT COUNT(*)
            FROM local.spotify.artist_listening_analytics
        """).collect()[0][0]
    )

    print()
    print("=" * 60)
    print("ARTIST ANALYTICS COMPLETE")
    print("=" * 60)

    spark.stop()


if __name__ == "__main__":
    main()