from query_prices import get_all_yahoo_instruments
from ingest_yahoo_prices import ingest_yahoo_prices


if __name__ == "__main__":
    instruments_df = get_all_yahoo_instruments()

    for _, row in instruments_df.iterrows():
        print(f"\nInitial load for {row['symbol']}...")

        ingest_yahoo_prices(
            db_symbol=row["symbol"],
            yahoo_symbol=row["yahoo_symbol"],
            start_date="2000-01-01",
            end_date="2026-05-09",
        )