from pathlib import Path
import pandas as pd
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "spotify_analytics",
    "user": "postgres",
    "password": "postgres",
}

GOLD_ROOT = Path("data/gold")


def get_latest_snapshot(table_name):
    table_root = GOLD_ROOT / table_name

    snapshots = sorted(
        [p for p in table_root.iterdir() if p.is_dir() and p.name.startswith("snapshot=")],
        reverse=True
    )

    if not snapshots:
        raise FileNotFoundError(f"No snapshots found for {table_name}")

    snapshot_dir = snapshots[0]
    snapshot_id = snapshot_dir.name.replace("snapshot=", "")
    parquet_file = snapshot_dir / f"{table_name}.parquet"

    return snapshot_id, parquet_file


def load_table(cursor, table_name, df):
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')

    columns = []

    for column in df.columns:
        if pd.api.types.is_integer_dtype(df[column]):
            sql_type = "BIGINT"
        elif pd.api.types.is_bool_dtype(df[column]):
            sql_type = "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(df[column]):
            sql_type = "TIMESTAMP WITH TIME ZONE"
        else:
            sql_type = "TEXT"

        columns.append(f'"{column}" {sql_type}')

    create_sql = f'''
        CREATE TABLE "{table_name}" (
            {", ".join(columns)}
        )
    '''

    cursor.execute(create_sql)

    column_names = ", ".join(f'"{c}"' for c in df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))

    insert_sql = f'''
        INSERT INTO "{table_name}" ({column_names})
        VALUES ({placeholders})
    '''

    for row in df.itertuples(index=False, name=None):
        values = [
            None if pd.isna(value) else value
            for value in row
        ]
        cursor.execute(insert_sql, values)

    print(f"Loaded {len(df)} rows → {table_name}")


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    tables = [
        "artist_summary",
        "album_summary",
        "saved_track_summary",
    ]

    snapshot_ids = []

    for table_name in tables:
        snapshot_id, parquet_file = get_latest_snapshot(table_name)

        print(f"\nReading {table_name}")
        print(f"Snapshot: {snapshot_id}")
        print(f"File: {parquet_file}")

        df = pd.read_parquet(parquet_file)

        snapshot_ids.append(snapshot_id)

        load_table(cursor, table_name, df)

    if len(set(snapshot_ids)) != 1:
        raise ValueError(
            f"Gold tables have different snapshots: {snapshot_ids}"
        )

    conn.commit()

    cursor.close()
    conn.close()

    print("\nPostgreSQL load completed successfully.")
    print(f"Snapshot loaded: {snapshot_ids[0]}")


if __name__ == "__main__":
    main()