from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    ArrayType,
    BooleanType,
    LongType,
    IntegerType,
    DoubleType,
)

KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"
KAFKA_TOPIC = "spotify-listening"

spark = (
    SparkSession.builder
    .appName("SpotifyKafkaToIceberg")
    .config(
        "spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1,"
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
spark.conf.set("spark.sql.streaming.metricsEnabled", "false")

schema = StructType([
    StructField("event_type", StringType()),
    StructField("track_id", StringType()),
    StructField("track_name", StringType()),
    StructField("artist_ids", ArrayType(StringType())),
    StructField("artist_names", ArrayType(StringType())),
    StructField("album_id", StringType()),
    StructField("album_name", StringType()),
    StructField("is_playing", BooleanType()),
    StructField("progress_ms", LongType()),
    StructField("duration_ms", LongType()),
    StructField("spotify_timestamp", LongType()),
    StructField("collected_at", StringType()),
])

raw_stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

events = (
    raw_stream
    .select(
        col("timestamp").alias("kafka_timestamp"),
        from_json(col("value").cast("string"), schema).alias("event")
    )
    .select(
        "kafka_timestamp",
        "event.*"
    )
    .filter(
        (col("event_type") == "now_playing") &
        col("track_id").isNotNull()
    )
    .withColumn(
        "progress_seconds",
        col("progress_ms") / 1000.0
    )
    .withColumn(
        "duration_seconds",
        col("duration_ms") / 1000.0
    )
    .withColumn(
        "progress_pct",
        (col("progress_ms") / col("duration_ms")) * 100
    )
    .withColumn(
        "collected_at_ts",
        to_timestamp(col("collected_at"))
    )
)

events = events.select(
    "kafka_timestamp",
    "collected_at_ts",
    "spotify_timestamp",
    "event_type",
    "track_id",
    "track_name",
    "artist_ids",
    "artist_names",
    "album_id",
    "album_name",
    "is_playing",
    "progress_ms",
    "duration_ms",
    "progress_seconds",
    "duration_seconds",
    "progress_pct",
)

spark.sql("""
CREATE TABLE IF NOT EXISTS local.spotify.listening_events (
    kafka_timestamp TIMESTAMP,
    collected_at_ts TIMESTAMP,
    spotify_timestamp BIGINT,
    event_type STRING,
    track_id STRING,
    track_name STRING,
    artist_ids ARRAY<STRING>,
    artist_names ARRAY<STRING>,
    album_id STRING,
    album_name STRING,
    is_playing BOOLEAN,
    progress_ms BIGINT,
    duration_ms BIGINT,
    progress_seconds DOUBLE,
    duration_seconds DOUBLE,
    progress_pct DOUBLE
)
USING iceberg
""")

query = (
    events
    .writeStream
    .format("iceberg")
    .outputMode("append")
    .option(
        "checkpointLocation",
        "data/checkpoints/spotify-listening"
    )
    .toTable("local.spotify.listening_events")
)

print("Spark → Iceberg streaming writer started.")
print("Listening to Kafka topic:", KAFKA_TOPIC)

query.awaitTermination()