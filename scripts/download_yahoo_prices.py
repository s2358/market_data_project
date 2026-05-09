import yfinance as yf


def download_prices(symbol, start_date, end_date):
    df = yf.download(
        symbol,
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df.columns = [
        col.lower().replace(" ", "_")
        for col in df.columns
    ]

    df = df.rename(columns={"adj_close": "adjusted_close"})

    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    return df


if __name__ == "__main__":
    symbol = "AAPL"
    start_date = "2020-01-01"
    end_date = "2025-01-01"

    df = download_prices(symbol, start_date, end_date)

    print(df.head())
    print()
    print(df.tail())
    print()
    print(df.columns)
    print()
    print(df.info())