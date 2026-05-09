import math

import pandas as pd
import pytest

from analytics.returns import calculate_return_std_dev, calculate_simple_returns


def test_calculate_simple_returns_happy_path():
    prices = pd.DataFrame({"adjusted_close": [100.0, 110.0, 121.0]})
    returns = calculate_simple_returns(prices)
    assert len(returns) == 2
    assert returns.iloc[0] == pytest.approx(0.10)
    assert returns.iloc[1] == pytest.approx(0.10)


def test_calculate_simple_returns_missing_column_raises():
    prices = pd.DataFrame({"close": [100.0, 101.0]})
    with pytest.raises(ValueError, match="Missing required price column"):
        calculate_simple_returns(prices, price_column="adjusted_close")


def test_calculate_return_std_dev_requires_enough_points_for_window():
    prices = pd.DataFrame({"adjusted_close": [100.0, 101.0, 102.0]})
    with pytest.raises(ValueError, match="At least 4 price points"):
        calculate_return_std_dev(prices, rolling_window=3)


def test_calculate_return_std_dev_annualization_scales_by_sqrt_time():
    prices = pd.DataFrame({"adjusted_close": [100.0, 103.0, 101.0, 105.0, 106.0, 104.0]})
    daily = calculate_return_std_dev(prices, annualize=False, rolling_window=3)
    annual = calculate_return_std_dev(
        prices,
        annualize=True,
        periods_per_year=252,
        rolling_window=3,
    )
    assert annual == pytest.approx(daily * math.sqrt(252), rel=1e-9)


def test_calculate_return_std_dev_invalid_periods_raises():
    prices = pd.DataFrame({"adjusted_close": [100.0, 102.0, 101.0, 103.0]})
    with pytest.raises(ValueError, match="periods_per_year must be positive"):
        calculate_return_std_dev(prices, periods_per_year=0, rolling_window=2)
