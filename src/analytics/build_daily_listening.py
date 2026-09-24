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
        .appName("SpotifyDailyListeningAnalytics")
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
    print("BUILDING DAILY LISTENING ANALYTICS")
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
    """)

    daily = (
        df
        .withColumn(
            "listening_date",
            F.to_date("collected_at_ts")
        )
        .withColumn(
            "hour",
            F.hour("collected_at_ts")
        )
        .groupBy("listening_date")
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
        .orderBy(F.desc("listening_date"))
    )

    daily.writeTo(
        "local.spotify.daily_listening_analytics"
    ).createOrReplace()

    print()
    print("TABLE:")
    print("local.spotify.daily_listening_analytics")

    print()
    print("SCHEMA:")
    spark.sql("""
        DESCRIBE local.spotify.daily_listening_analytics
    """).show(truncate=False)

    print()
    print("DATA:")
    spark.sql("""
        SELECT *
        FROM local.spotify.daily_listening_analytics
        ORDER BY listening_date DESC
    """).show(20, truncate=False)

    print()
    print(
        "Rows:",
        spark.sql("""
            SELECT COUNT(*)
            FROM local.spotify.daily_listening_analytics
        """).collect()[0][0]
    )

    print()
    print("=" * 60)
    print("DAILY ANALYTICS COMPLETE")
    print("=" * 60)

    spark.stop()


if __name__ == "__main__":
    main()