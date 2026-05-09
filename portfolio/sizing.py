from typing import Optional

import pandas as pd


def calculate_notional_exposure_home_ccy(
    annual_instrument_risk: float,
    capital_home_ccy: float = 3000.0,
    target_risk: float = 0.12,
) -> float:
    if annual_instrument_risk <= 0:
        raise ValueError("annual_instrument_risk must be positive.")
    if capital_home_ccy <= 0:
        raise ValueError("capital_home_ccy must be positive.")
    if target_risk <= 0:
        raise ValueError("target_risk must be positive.")

    return (target_risk * capital_home_ccy) / annual_instrument_risk


def calculate_position_size(
    asset_type: str,
    notional_exposure_home_ccy: float,
    fx_rate: float,
    latest_price: Optional[float] = None,
) -> float:
    if notional_exposure_home_ccy <= 0:
        raise ValueError("notional_exposure_home_ccy must be positive.")
    if fx_rate <= 0:
        raise ValueError("fx_rate must be positive.")

    normalized_asset_type = asset_type.lower()

    if normalized_asset_type == "fx":
        return notional_exposure_home_ccy * fx_rate

    if latest_price is None or latest_price <= 0:
        raise ValueError("latest_price must be positive for non-FX instruments.")

    return (notional_exposure_home_ccy * fx_rate) / latest_price


def build_portfolio_sizing_row(
    symbol: str,
    asset_type: str,
    annual_instrument_risk: float,
    capital_home_ccy: float,
    target_risk: float,
    fx_rate: float,
    latest_price: Optional[float],
) -> dict:
    exposure_home_ccy = calculate_notional_exposure_home_ccy(
        annual_instrument_risk=annual_instrument_risk,
        capital_home_ccy=capital_home_ccy,
        target_risk=target_risk,
    )

    position_size = calculate_position_size(
        asset_type=asset_type,
        notional_exposure_home_ccy=exposure_home_ccy,
        fx_rate=fx_rate,
        latest_price=latest_price,
    )

    row = {
        "symbol": symbol,
        "asset_type": asset_type,
        "instrument_risk_annual": annual_instrument_risk,
        "target_risk": target_risk,
        "capital_sgd": capital_home_ccy,
        "notional_exposure_sgd": exposure_home_ccy,
    }

    if asset_type.lower() == "fx":
        row["fx_exposure_instrument_ccy"] = position_size
    else:
        row["latest_price"] = latest_price
        row["position_size_shares"] = position_size

    return row


def build_portfolio_sizing_table(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def calculate_stop_loss_gap(
    annual_instrument_risk: float,
    current_price: float,
    trailing_stop_loss_factor: float = 0.5,
) -> float:
    if annual_instrument_risk <= 0:
        raise ValueError("annual_instrument_risk must be positive.")
    if current_price <= 0:
        raise ValueError("current_price must be positive.")
    if trailing_stop_loss_factor <= 0:
        raise ValueError("trailing_stop_loss_factor must be positive.")

    std_dev_price_points = annual_instrument_risk * current_price
    stop_loss_gap = std_dev_price_points * trailing_stop_loss_factor

    return stop_loss_gap


def _adjust_if_round_number(
    stop_loss_level: float,
    position: str,
    tick_size: float = 0.01,
    decimals: int = 2,
) -> float:
    rounded_stop = round(stop_loss_level, decimals)
    fraction = rounded_stop - int(rounded_stop)

    # Avoid exact round-number levels like 300.00.
    if abs(fraction) < 1e-12:
        if position == "long":
            rounded_stop -= tick_size
        else:
            rounded_stop += tick_size

    return round(rounded_stop, decimals)


def calculate_stop_loss_level(
    position: str,
    initial_entry_price: float,
    stop_loss_gap: float,
    tick_size: float = 0.01,
) -> float:
    normalized_position = position.lower()
    if normalized_position not in {"long", "short"}:
        raise ValueError("position must be either 'long' or 'short'.")
    if initial_entry_price <= 0:
        raise ValueError("initial_entry_price must be positive.")
    if stop_loss_gap <= 0:
        raise ValueError("stop_loss_gap must be positive.")
    if tick_size <= 0:
        raise ValueError("tick_size must be positive.")

    if normalized_position == "long":
        raw_stop_loss_level = initial_entry_price - stop_loss_gap
    else:
        raw_stop_loss_level = initial_entry_price + stop_loss_gap

    return _adjust_if_round_number(
        stop_loss_level=raw_stop_loss_level,
        position=normalized_position,
        tick_size=tick_size,
        decimals=2,
    )
