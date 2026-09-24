from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json,
    col,
    round,
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    ArrayType,
    BooleanType,
    LongType,
)

KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"
KAFKA_TOPIC = "spotify-listening"

spark = (
    SparkSession.builder
    .appName("SpotifyKafkaStreaming")
    .master("local[*]")
    .config(
        "spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1"
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

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

df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

events = (
    df.select(
        col("timestamp").alias("kafka_timestamp"),
        from_json(
            col("value").cast("string"),
            schema
        ).alias("event")
    )
    .select(
        "kafka_timestamp",
        "event.*"
    )
)

clean_events = (
    events
    .filter(col("is_playing") == True)
    .filter(col("track_id").isNotNull())
    .withColumn(
        "progress_seconds",
        round(col("progress_ms") / 1000, 3)
    )
    .withColumn(
        "duration_seconds",
        round(col("duration_ms") / 1000, 3)
    )
    .withColumn(
        "progress_pct",
        round(
            (col("progress_ms") / col("duration_ms")) * 100,
            2
        )
    )
    .select(
        "kafka_timestamp",
        "collected_at",
        "spotify_timestamp",
        "event_type",
        "track_id",
        "track_name",
        "artist_ids",
        "artist_names",
        "album_id",
        "album_name",
        "is_playing",
        "progress_seconds",
        "duration_seconds",
        "progress_pct",
    )
)

query = (
    clean_events.writeStream
    .format("console")
    .outputMode("append")
    .option("truncate", "false")
    .option("numRows", 10)
    .start()
)

query.awaitTermination()
