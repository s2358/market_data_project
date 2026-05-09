from ingest_yahoo_prices import update_missing_yahoo_prices


if __name__ == "__main__":
    update_missing_yahoo_prices(
        db_symbol="AAPL",
        yahoo_symbol="AAPL",
    )

    update_missing_yahoo_prices(
        db_symbol="EURUSD",
        yahoo_symbol="EURUSD=X",
    )

    update_missing_yahoo_prices(
    db_symbol="SPY",
    yahoo_symbol="SPY",
    )
