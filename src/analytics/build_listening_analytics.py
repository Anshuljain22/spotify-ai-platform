from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    count,
    max,
    col,
    concat_ws,
)

spark = (
    SparkSession.builder
    .appName("SpotifyListeningAnalytics")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-4.1_2.13:1.11.0"
    )
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
        "data/iceberg"
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

events = spark.table("local.spotify.listening_events")

analytics = (
    events
    .filter(col("is_playing") == True)
    .groupBy(
        "track_id",
        "track_name",
        concat_ws(", ", col("artist_names")).alias("artists")
    )
    .agg(
        count("*").alias("play_events"),
        avg("progress_pct").alias("avg_progress_pct"),
        max("collected_at_ts").alias("latest_played_at")
    )
    .orderBy(col("play_events").desc())
)

analytics.show(20, truncate=False)

spark.sql("""
CREATE TABLE IF NOT EXISTS local.spotify.listening_analytics (
    track_id STRING,
    track_name STRING,
    artists STRING,
    play_events BIGINT,
    avg_progress_pct DOUBLE,
    latest_played_at TIMESTAMP
)
USING iceberg
""")

analytics.writeTo(
    "local.spotify.listening_analytics"
).overwritePartitions()

print("Analytics table created successfully.")

spark.stop()