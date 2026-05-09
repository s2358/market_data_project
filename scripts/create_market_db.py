import sqlite3
from pathlib import Path


DB_PATH = Path("data/market_data.sqlite")


def create_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments (
        instrument_id INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        exchange TEXT,
        currency TEXT NOT NULL,
        name TEXT,
        base_currency TEXT,
        quote_currency TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(symbol, asset_type, exchange)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data_sources (
        source_id INTEGER PRIMARY KEY,
        source_name TEXT NOT NULL UNIQUE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_prices (
        price_id INTEGER PRIMARY KEY,
        instrument_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL,
        price_date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL NOT NULL,
        adjusted_close REAL NOT NULL,
        volume REAL,
        currency TEXT NOT NULL,
        is_adjusted INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id),
        FOREIGN KEY (source_id) REFERENCES data_sources(source_id),

        UNIQUE(instrument_id, source_id, price_date)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_log (
        log_id INTEGER PRIMARY KEY,
        source_id INTEGER NOT NULL,
        instrument_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        rows_inserted INTEGER,
        status TEXT,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (source_id) REFERENCES data_sources(source_id),
        FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id)
    );
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_prices_instrument_date
    ON daily_prices (instrument_id, price_date);
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_prices_source_date
    ON daily_prices (source_id, price_date);
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_instruments_symbol
    ON instruments (symbol, asset_type);
    """)

    cursor.executemany("""
    INSERT OR IGNORE INTO data_sources (source_name)
    VALUES (?);
    """, [("yahoo",), ("moomoo",)])

    conn.commit()
    conn.close()

    print(f"Database created at: {DB_PATH}")


if __name__ == "__main__":
    create_database()