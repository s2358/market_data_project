import pytest

from portfolio.sizing import (
    calculate_notional_exposure_home_ccy,
    calculate_position_size,
    calculate_stop_loss_gap,
    calculate_stop_loss_level,
)


def test_calculate_notional_exposure_home_ccy():
    result = calculate_notional_exposure_home_ccy(
        annual_instrument_risk=0.20,
        capital_home_ccy=3000.0,
        target_risk=0.12,
    )
    assert result == pytest.approx(1800.0)


def test_calculate_position_size_fx():
    result = calculate_position_size(
        asset_type="fx",
        notional_exposure_home_ccy=1000.0,
        fx_rate=0.74,
    )
    assert result == pytest.approx(740.0)


def test_calculate_position_size_equity():
    result = calculate_position_size(
        asset_type="equity",
        notional_exposure_home_ccy=1000.0,
        fx_rate=0.74,
        latest_price=185.0,
    )
    assert result == pytest.approx(4.0)


def test_calculate_stop_loss_gap():
    result = calculate_stop_loss_gap(
        annual_instrument_risk=0.20,
        current_price=100.0,
        trailing_stop_loss_factor=0.5,
    )
    assert result == pytest.approx(10.0)


def test_calculate_stop_loss_level_long_round_number_adjustment():
    # Raw long stop would be 300.00, should be shifted to 299.99.
    result = calculate_stop_loss_level(
        position="long",
        initial_entry_price=310.0,
        stop_loss_gap=10.0,
    )
    assert result == pytest.approx(299.99)


def test_calculate_stop_loss_level_short_round_number_adjustment():
    # Raw short stop would be 300.00, should be shifted to 300.01.
    result = calculate_stop_loss_level(
        position="short",
        initial_entry_price=290.0,
        stop_loss_gap=10.0,
    )
    assert result == pytest.approx(300.01)


def test_calculate_stop_loss_level_invalid_position():
    with pytest.raises(ValueError, match="position must be either 'long' or 'short'"):
        calculate_stop_loss_level(
            position="flat",
            initial_entry_price=100.0,
            stop_loss_gap=5.0,
        )
