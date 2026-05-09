import sqlite3
from pathlib import Path


DB_PATH = Path("data/market_data.sqlite")


INSTRUMENTS = [
    {
        "symbol": "AAPL",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "name": "Apple Inc.",
        "base_currency": None,
        "quote_currency": None,
    },
    {
        "symbol": "EURUSD",
        "asset_type": "fx",
        "exchange": "FX",
        "currency": "USD",
        "name": "EUR/USD Spot",
        "base_currency": "EUR",
        "quote_currency": "USD",
    },
    {
        "symbol": "SPY",
        "asset_type": "etf",
        "exchange": "NYSEARCA",
        "currency": "USD",
        "name": "SPDR S&P 500 ETF Trust",
        "base_currency": None,
        "quote_currency": None,
    },
]


def insert_instruments():
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()

        for instrument in INSTRUMENTS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO instruments (
                    symbol,
                    asset_type,
                    exchange,
                    currency,
                    name,
                    base_currency,
                    quote_currency
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    instrument["symbol"],
                    instrument["asset_type"],
                    instrument["exchange"],
                    instrument["currency"],
                    instrument["name"],
                    instrument["base_currency"],
                    instrument["quote_currency"],
                ),
            )

            print(
                f"Processed instrument: "
                f"{instrument['symbol']} - {instrument['name']}"
            )

        conn.commit()

        print("\nInstrument insertion complete.")

    finally:
        conn.close()


if __name__ == "__main__":
    insert_instruments()