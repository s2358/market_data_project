import math

import pandas as pd


def calculate_simple_returns(
    prices_df: pd.DataFrame,
    price_column: str = "adjusted_close",
) -> pd.Series:
    if prices_df is None or prices_df.empty:
        raise ValueError("Price data is empty.")

    if price_column not in prices_df.columns:
        raise ValueError(f"Missing required price column: {price_column}")

    price_series = pd.to_numeric(prices_df[price_column], errors="coerce").dropna()

    if len(price_series) < 2:
        raise ValueError("At least 2 valid price points are required to compute returns.")

    returns = price_series.pct_change(fill_method=None).dropna()
    returns = returns[returns.notna() & returns.map(math.isfinite)]

    if returns.empty:
        raise ValueError("No valid returns could be computed from price data.")

    return returns


def calculate_return_std_dev(
    prices_df: pd.DataFrame,
    price_column: str = "adjusted_close",
    annualize: bool = False,
    periods_per_year: int = 252,
    rolling_window: int = 25,
) -> float:
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")
    if rolling_window <= 1:
        raise ValueError("rolling_window must be greater than 1.")

    returns = calculate_simple_returns(
        prices_df=prices_df,
        price_column=price_column,
    )

    if len(returns) < rolling_window:
        raise ValueError(
            f"At least {rolling_window + 1} price points are required "
            f"to compute a {rolling_window}-day rolling standard deviation."
        )

    rolling_std = returns.rolling(window=rolling_window).std(ddof=1).dropna()

    if rolling_std.empty:
        raise ValueError(
            f"Unable to compute {rolling_window}-day rolling standard deviation "
            "from available returns."
        )

    std_dev = rolling_std.iloc[-1]

    if annualize:
        std_dev *= math.sqrt(periods_per_year)

    return float(std_dev)
