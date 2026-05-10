import sqlite3
from pathlib import Path

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = _PROJECT_ROOT / "data" / "market_data.sqlite"


def get_instrument_symbols():
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT symbol
            FROM instruments
            ORDER BY symbol;
            """
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def get_instrument_symbol_name_map():
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT symbol, name
            FROM instruments;
            """
        )
        return {
            row[0]: (row[1] or "").strip()
            for row in cursor.fetchall()
        }
    finally:
        conn.close()


def get_all_yahoo_instruments():
    conn = sqlite3.connect(DB_PATH)

    try:
        query = """
        SELECT
            symbol,
            yahoo_symbol
        FROM instruments
        WHERE yahoo_symbol IS NOT NULL
        ORDER BY symbol;
        """

        df = pd.read_sql_query(query, conn)

        return df

    finally:
        conn.close()

def get_prices(symbol, start_date=None, end_date=None, source_name="yahoo"):
    conn = sqlite3.connect(DB_PATH)

    try:
        query = """
        SELECT
            p.price_date,
            i.symbol,
            i.asset_type,
            s.source_name,
            p.open,
            p.high,
            p.low,
            p.close,
            p.adjusted_close,
            p.volume,
            p.currency
        FROM daily_prices p
        JOIN instruments i
            ON p.instrument_id = i.instrument_id
        JOIN data_sources s
            ON p.source_id = s.source_id
        WHERE i.symbol = ?
          AND s.source_name = ?
        """

        params = [symbol, source_name]

        if start_date is not None:
            query += " AND p.price_date >= ?"
            params.append(start_date)

        if end_date is not None:
            query += " AND p.price_date <= ?"
            params.append(end_date)

        query += " ORDER BY p.price_date;"

        df = pd.read_sql_query(
            query,
            conn,
            params=params,
            parse_dates=["price_date"],
        )

        return df

    finally:
        conn.close()


def get_latest_price_date(symbol, source_name="yahoo"):
    conn = sqlite3.connect(DB_PATH)

    try:
        query = """
        SELECT MAX(p.price_date)
        FROM daily_prices p
        JOIN instruments i
            ON p.instrument_id = i.instrument_id
        JOIN data_sources s
            ON p.source_id = s.source_id
        WHERE i.symbol = ?
          AND s.source_name = ?;
        """

        cursor = conn.cursor()
        cursor.execute(query, (symbol, source_name))

        result = cursor.fetchone()

        return result[0]

    finally:
        conn.close()


if __name__ == "__main__":
    df = get_prices(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2025-01-01",
    )

    print(df.head())
    print()
    print(df.tail())
    print()
    print(df.info())
    print()

    latest_date = get_latest_price_date("AAPL")
    print(f"Latest AAPL date in database: {latest_date}")

    latest_fx_date = get_latest_price_date("EURUSD")
    print(f"Latest EURUSD date in database: {latest_fx_date}")