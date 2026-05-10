from query_prices import get_all_yahoo_instruments
from ingest_yahoo_prices import update_missing_yahoo_prices


if __name__ == "__main__":
    instruments_df = get_all_yahoo_instruments()

    for _, row in instruments_df.iterrows():
        print(f"\nUpdating {row['symbol']}...")

        update_missing_yahoo_prices(
            db_symbol=row["symbol"],
            yahoo_symbol=row["yahoo_symbol"],
        )