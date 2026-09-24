from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


WAREHOUSE = "data/iceberg"

ICEBERG_PACKAGE = (
    "org.apache.iceberg:"
    "iceberg-spark-runtime-4.1_2.13:"
    "1.11.0"
)


def get_spark():
    return (
        SparkSession.builder
        .appName("SpotifyListeningConcentration")
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

    spark.sparkContext.setLogLevel("WARN")

    print("=" * 60)
    print("BUILDING LISTENING CONCENTRATION ANALYTICS")
    print("=" * 60)

    events = spark.sql("""
        SELECT
            artist_names
        FROM local.spotify.listening_events
        WHERE is_playing = true
          AND artist_names IS NOT NULL
    """)

    artist_df = (
        events
        .withColumn("artist", F.explode("artist_names"))
        .groupBy("artist")
        .agg(
            F.count("*").alias("play_events")
        )
    )

    total_events = (
        artist_df
        .agg(F.sum("play_events").alias("total_events"))
        .collect()[0]["total_events"]
    )

    if not total_events:
        print("No listening events found.")
        spark.stop()
        return

    window = Window.orderBy(F.desc("play_events"))

    ranked = (
        artist_df
        .withColumn(
            "rank",
            F.row_number().over(window)
        )
        .withColumn(
            "share_pct",
            F.round(
                (F.col("play_events") / F.lit(total_events)) * 100,
                2
            )
        )
    )

    top_artist = (
        ranked
        .filter(F.col("rank") == 1)
        .select(
            "artist",
            "play_events",
            "share_pct"
        )
        .collect()[0]
    )

    top_3_share = (
        ranked
        .filter(F.col("rank") <= 3)
        .agg(
            F.round(
                F.sum("share_pct"),
                2
            ).alias("share")
        )
        .collect()[0]["share"]
    )

    top_5_share = (
        ranked
        .filter(F.col("rank") <= 5)
        .agg(
            F.round(
                F.sum("share_pct"),
                2
            ).alias("share")
        )
        .collect()[0]["share"]
    )

    summary = spark.createDataFrame(
        [
            (
                int(total_events),
		top_artist["artist"],
		int(top_artist["play_events"]),
		float(top_artist["share_pct"]),
		float(top_3_share),
		float(top_5_share),
            )
        ],
        [
            "total_events",
            "top_artist",
            "top_artist_events",
            "top_artist_association_share_pct",
            "top_3_artist_association_share_pct",
            "top_5_artist_association_share_pct",
        ]
    )

    summary.writeTo(
        "local.spotify.listening_concentration"
    ).createOrReplace()

    print()
    print("TABLE:")
    print("local.spotify.listening_concentration")

    print()
    print("RESULT (ARTIST ASSOCIATIONS):")
    summary.show(truncate=False)

    print()
    print("TOP ARTISTS:")

    ranked.select(
        "rank",
        "artist",
        "play_events",
        "share_pct"
    ).show(10, truncate=False)

    print()
    print("=" * 60)
    print("LISTENING CONCENTRATION COMPLETE")
    print("=" * 60)

    spark.stop()


if __name__ == "__main__":
    main()