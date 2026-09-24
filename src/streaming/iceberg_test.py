from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("SpotifyIcebergTest")
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

spark.sql("CREATE NAMESPACE IF NOT EXISTS local.spotify")

spark.sql("""
    CREATE TABLE IF NOT EXISTS local.spotify.test_tracks (
        track_id STRING,
        track_name STRING,
        artist_name STRING
    ) USING iceberg
""")

data = [
    ("track_001", "Test Song", "Test Artist"),
    ("track_002", "Another Song", "Another Artist")
]

df = spark.createDataFrame(
    data,
    ["track_id", "track_name", "artist_name"]
)

df.writeTo("local.spotify.test_tracks").append()

print("\n=== ICEBERG TABLE ===")
spark.sql("SELECT * FROM local.spotify.test_tracks").show()

print("\n=== TABLE HISTORY ===")
spark.sql("SELECT * FROM local.spotify.test_tracks.history").show()

spark.stop()