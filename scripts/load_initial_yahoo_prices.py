from ingest_yahoo_prices import ingest_yahoo_prices


if __name__ == "__main__":
    ingest_yahoo_prices(
        db_symbol="SPY",
        yahoo_symbol="SPY",
        start_date="2000-01-01",
        end_date="2026-05-09",
    )