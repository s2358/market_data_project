import pandas as pd
import pytest

from analytics.moving_average import calculate_ma_signal


def test_calculate_ma_signal_long_short_flat_positions():
    prices = pd.DataFrame(
        {
            "price_date": pd.to_datetime(
                [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-06",
                ]
            ),
            "adjusted_close": [10.0, 10.0, 10.0, 12.0, 8.0, 8.0],
        }
    )
    result = calculate_ma_signal(prices, fast_window=2, slow_window=3)
    signal_col = "signal_ma_2_3"
    recent = result.dropna(subset=[signal_col]).reset_index(drop=True)
    positions = set(recent["position"].tolist())
    assert "long" in positions
    assert "short" in positions
    assert "flat" in positions


def test_calculate_ma_signal_sorts_by_price_date():
    prices = pd.DataFrame(
        {
            "price_date": pd.to_datetime(["2024-01-03", "2024-01-01", "2024-01-02"]),
            "adjusted_close": [102.0, 100.0, 101.0],
        }
    )
    result = calculate_ma_signal(prices, fast_window=1, slow_window=2)
    assert list(result["price_date"]) == sorted(result["price_date"].tolist())


def test_calculate_ma_signal_fast_window_must_be_smaller():
    prices = pd.DataFrame({"adjusted_close": [100.0, 101.0, 102.0]})
    with pytest.raises(ValueError, match="fast_window must be smaller than slow_window"):
        calculate_ma_signal(prices, fast_window=5, slow_window=5)


def test_calculate_ma_signal_flat_position_when_signal_zero():
    prices = pd.DataFrame({"adjusted_close": [10.0, 10.0, 10.0, 10.0]})
    result = calculate_ma_signal(prices, fast_window=2, slow_window=3)
    signal_col = "signal_ma_2_3"
    latest = result.dropna(subset=[signal_col]).iloc[-1]
    assert latest[signal_col] == pytest.approx(0.0)
    assert latest["position"] == "flat"
