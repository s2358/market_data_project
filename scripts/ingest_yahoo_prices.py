import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from query_prices import get_latest_price_date
from download_yahoo_prices import download_prices


DB_PATH = Path("data/market_data.sqlite")


def get_id(cursor, table, id_column, lookup_column, lookup_value):
    cursor.execute(
        f"""
        SELECT {id_column}
        FROM {table}
        WHERE {lookup_column} = ?;
        """,
        (lookup_value,),
    )

    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"{lookup_value} not found in {table}")

    return result[0]


def get_instrument(cursor, db_symbol):
    cursor.execute(
        """
        SELECT instrument_id, currency
        FROM instruments
        WHERE symbol = ?;
        """,
        (db_symbol,),
    )

    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"{db_symbol} not found in instruments table")

    return result


def get_latest_yahoo_date(yahoo_symbol):
    today = datetime.today()
    lookback_start = today - timedelta(days=14)

    df = download_prices(
        symbol=yahoo_symbol,
        start_date=lookback_start.strftime("%Y-%m-%d"),
        end_date=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
    )

    required_non_null_columns = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "adjusted_close",
    ]

    df = df.dropna(subset=required_non_null_columns)

    if df.empty:
        raise ValueError(f"No recent usable Yahoo data found for {yahoo_symbol}")

    return df["date"].max().strftime("%Y-%m-%d")


def ingest_yahoo_prices(db_symbol, yahoo_symbol, start_date, end_date):
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        df = download_prices(yahoo_symbol, start_date, end_date)

        required_columns = {
            "date",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
        }

        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        required_non_null_columns = [
            "date",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
        ]

        df = df.dropna(subset=required_non_null_columns)

        if df.empty:
            raise ValueError(
                f"No usable price rows after dropping missing values for {yahoo_symbol}"
            )

        instrument_id, currency = get_instrument(cursor, db_symbol)

        source_id = get_id(
            cursor=cursor,
            table="data_sources",
            id_column="source_id",
            lookup_column="source_name",
            lookup_value="yahoo",
        )

        rows = []

        for _, row in df.iterrows():
            if row["high"] < row["low"]:
                raise ValueError(
                    f"Invalid OHLC data for {db_symbol} on {row['date']}: "
                    "high is lower than low"
                )

            volume = None if row["volume"] != row["volume"] else float(row["volume"])

            rows.append(
                (
                    instrument_id,
                    source_id,
                    row["date"].strftime("%Y-%m-%d"),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["adjusted_close"]),
                    volume,
                    currency,
                    1,
                )
            )

        cursor.executemany(
            """
            INSERT INTO daily_prices (
                instrument_id,
                source_id,
                price_date,
                open,
                high,
                low,
                close,
                adjusted_close,
                volume,
                currency,
                is_adjusted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(instrument_id, source_id, price_date)
            DO UPDATE SET
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                adjusted_close = excluded.adjusted_close,
                volume = excluded.volume,
                currency = excluded.currency,
                is_adjusted = excluded.is_adjusted;
            """,
            rows,
        )

        conn.commit()

        print(f"Inserted/updated {len(rows)} rows for {db_symbol} from {yahoo_symbol}")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def update_missing_yahoo_prices(db_symbol, yahoo_symbol):
    db_latest = get_latest_price_date(db_symbol)
    yahoo_latest = get_latest_yahoo_date(yahoo_symbol)

    print(f"DB latest date for {db_symbol}: {db_latest}")
    print(f"Yahoo latest date for {yahoo_symbol}: {yahoo_latest}")

    if db_latest is not None and db_latest >= yahoo_latest:
        print(f"{db_symbol} is already up to date.")
        return

    if db_latest is None:
        start_date = "1900-01-01"
    else:
        latest_dt = datetime.strptime(db_latest, "%Y-%m-%d")
        start_date = (latest_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    yahoo_latest_dt = datetime.strptime(yahoo_latest, "%Y-%m-%d")
    end_date = (yahoo_latest_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    ingest_yahoo_prices(
        db_symbol=db_symbol,
        yahoo_symbol=yahoo_symbol,
        start_date=start_date,
        end_date=end_date,
    )