import pandas as pd


def calculate_ma_signal(
    prices_df: pd.DataFrame,
    price_column: str = "adjusted_close",
    fast_window: int = 16,
    slow_window: int = 64,
) -> pd.DataFrame:
    if prices_df is None or prices_df.empty:
        raise ValueError("Price data is empty.")
    if price_column not in prices_df.columns:
        raise ValueError(f"Missing required price column: {price_column}")
    if fast_window <= 0 or slow_window <= 0:
        raise ValueError("Moving-average windows must be positive.")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window.")

    result_df = prices_df.copy()
    if "price_date" in result_df.columns:
        result_df = result_df.sort_values("price_date").reset_index(drop=True)

    price_series = pd.to_numeric(result_df[price_column], errors="coerce")

    result_df[f"ma_{fast_window}"] = price_series.rolling(
        window=fast_window,
        min_periods=fast_window,
    ).mean()
    result_df[f"ma_{slow_window}"] = price_series.rolling(
        window=slow_window,
        min_periods=slow_window,
    ).mean()

    signal_column = f"signal_ma_{fast_window}_{slow_window}"
    result_df[signal_column] = result_df[f"ma_{fast_window}"] - result_df[f"ma_{slow_window}"]

    result_df["position"] = pd.NA
    result_df.loc[result_df[signal_column] > 0, "position"] = "long"
    result_df.loc[result_df[signal_column] < 0, "position"] = "short"
    result_df.loc[result_df[signal_column] == 0, "position"] = "flat"

    return result_df
