
from pyspark.sql import SparkSession


WAREHOUSE = "data/iceberg"

ICEBERG_PACKAGE = (
    "org.apache.iceberg:"
    "iceberg-spark-runtime-4.1_2.13:"
    "1.11.0"
)


def get_spark():
    return (
        SparkSession.builder
        .appName("SpotifyIcebergOrganization")

        # ----------------------------------------------------
        # ICEBERG
        # ----------------------------------------------------

        .config(
            "spark.jars.packages",
            ICEBERG_PACKAGE
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
            WAREHOUSE
        )

        .getOrCreate()
    )


def main():
    spark = get_spark()

    # Spark 4.1.1 + Kafka metrics workaround
    spark.conf.set(
        "spark.sql.streaming.metricsEnabled",
        "false"
    )

    print("=" * 60)
    print("ICEBERG TABLE ORGANIZATION")
    print("=" * 60)

    # --------------------------------------------------------
    # CATALOG / NAMESPACE
    # --------------------------------------------------------

    spark.sql("""
        CREATE NAMESPACE IF NOT EXISTS local.spotify
    """)

    print("Namespace : local.spotify")

    # --------------------------------------------------------
    # LISTENING EVENTS TABLE
    # --------------------------------------------------------

    table_name = "local.spotify.listening_events"

    if not spark.catalog.tableExists(table_name):
        print()
        print("Table does not exist yet.")
        print("Run the streaming pipeline first.")
        spark.stop()
        return

    # --------------------------------------------------------
    # TABLE PROPERTIES
    # --------------------------------------------------------

    spark.sql(f"""
        ALTER TABLE {table_name}
        SET TBLPROPERTIES (
            'format-version' = '2',
            'write.format.default' = 'parquet',
            'write.parquet.compression-codec' = 'snappy'
        )
    """)

    print("Table properties updated.")

    # --------------------------------------------------------
    # TABLE INFORMATION
    # --------------------------------------------------------

    print()
    print("TABLE:")
    print(table_name)

    print()
    print("SCHEMA:")

    spark.sql(
        f"DESCRIBE TABLE {table_name}"
    ).show(
        truncate=False
    )

    # --------------------------------------------------------
    # SNAPSHOT HISTORY
    # --------------------------------------------------------

    print()
    print("SNAPSHOT HISTORY:")

    spark.sql(f"""
        SELECT
            committed_at,
            snapshot_id,
            operation,
            summary
        FROM {table_name}.snapshots
        ORDER BY committed_at DESC
    """).show(
        truncate=False
    )

    # --------------------------------------------------------
    # CURRENT RECORD COUNT
    # --------------------------------------------------------

    count = spark.sql(f"""
        SELECT COUNT(*) AS total_events
        FROM {table_name}
    """).collect()[0]["total_events"]

    print()
    print(f"Current events : {count}")

    print()
    print("=" * 60)
    print("ICEBERG ORGANIZATION COMPLETE")
    print("=" * 60)

    spark.stop()


if __name__ == "__main__":
    main()
