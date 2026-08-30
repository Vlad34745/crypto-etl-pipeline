"""
SQLite persistence layer for the crypto ETL pipeline.

This is the source of truth for historical data. crypto_history.xlsx is
regenerated from this database on every run — it's an export/report
artifact, not where data actually lives. That avoids the fragility of
using a spreadsheet as a database (full-file rewrites, no real
constraints, slow as history grows).
"""

import sqlite3

import pandas as pd

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    current_price REAL NOT NULL,
    market_cap REAL,
    total_volume REAL,
    price_change_percentage_24h REAL,
    snapshot_time TEXT NOT NULL,
    UNIQUE(symbol, snapshot_time)
);
"""


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(config.DB_FILE)


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_snapshot(df: pd.DataFrame) -> int:
    """Insert new rows, silently skipping any that violate the
    (symbol, snapshot_time) uniqueness constraint. Returns the number of
    rows actually inserted (i.e. excluding duplicates).
    """
    init_db()
    conn = get_connection()
    inserted = 0
    try:
        cur = conn.cursor()
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT OR IGNORE INTO snapshots
                    (name, symbol, current_price, market_cap, total_volume,
                     price_change_percentage_24h, snapshot_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["name"], row["symbol"], row["current_price"], row["market_cap"],
                    row["total_volume"], row["price_change_percentage_24h"], row["snapshot_time"],
                ),
            )
            inserted += cur.rowcount
        conn.commit()
    finally:
        conn.close()
    return inserted


def load_history() -> pd.DataFrame:
    """Return the full historical dataset, sorted by coin name then time."""
    init_db()
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT name, symbol, current_price, market_cap, total_volume, "
            "price_change_percentage_24h, snapshot_time FROM snapshots "
            "ORDER BY name, snapshot_time",
            conn,
        )
    finally:
        conn.close()
    return df
