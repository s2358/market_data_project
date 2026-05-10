import importlib.util
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.moving_average import calculate_ma_signal
from analytics.returns import calculate_return_std_dev

_query_prices_path = SCRIPTS_DIR / "query_prices.py"
_query_prices_spec = importlib.util.spec_from_file_location(
    "market_data_query_prices",
    _query_prices_path,
)
if _query_prices_spec is None or _query_prices_spec.loader is None:
    raise ImportError(f"Cannot load query_prices from {_query_prices_path}")
_query_prices = importlib.util.module_from_spec(_query_prices_spec)
_query_prices_spec.loader.exec_module(_query_prices)

get_instrument_symbols = _query_prices.get_instrument_symbols
get_instrument_symbol_name_map = _query_prices.get_instrument_symbol_name_map
get_prices = _query_prices.get_prices

PORTFOLIO_SIZING_PATH = PROJECT_ROOT / "portfolio" / "sizing.py"
portfolio_spec = importlib.util.spec_from_file_location(
    "market_data_portfolio_sizing",
    PORTFOLIO_SIZING_PATH,
)
if portfolio_spec is None or portfolio_spec.loader is None:
    raise ImportError(f"Unable to load portfolio module from {PORTFOLIO_SIZING_PATH}")
portfolio_module = importlib.util.module_from_spec(portfolio_spec)
portfolio_spec.loader.exec_module(portfolio_module)

build_portfolio_sizing_row = portfolio_module.build_portfolio_sizing_row
build_portfolio_sizing_table = portfolio_module.build_portfolio_sizing_table
calculate_stop_loss_gap = portfolio_module.calculate_stop_loss_gap
calculate_stop_loss_level = portfolio_module.calculate_stop_loss_level


WATCHED_DIRECTORIES = ["analytics", "portfolio", "dashboards", "scripts", "tests"]


def get_latest_python_mtime(project_root: Path) -> float:
    latest_mtime = 0.0
    for relative_dir in WATCHED_DIRECTORIES:
        target_dir = project_root / relative_dir
        if not target_dir.exists():
            continue
        for path in target_dir.rglob("*.py"):
            latest_mtime = max(latest_mtime, path.stat().st_mtime)
    return latest_mtime


def run_test_suite() -> tuple[bool, str]:
    command = [sys.executable, "-m", "pytest", "-q"]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip() or "No test output."


st.set_page_config(
    page_title="Market Data Dashboard",
    layout="wide",
)

db_symbols = get_instrument_symbols()

if not db_symbols:
    st.error(
        "No instruments found in the database. "
        "Create the DB and run `python scripts/insert_instruments.py` from the project root."
    )
    st.stop()

symbol = st.sidebar.selectbox(
    "Symbol",
    db_symbols,
)

symbols_for_table = st.sidebar.multiselect(
    "Symbols for volatility table",
    db_symbols,
    default=list(db_symbols),
)

portfolio_symbols = st.sidebar.multiselect(
    "Symbols for portfolio sizing",
    db_symbols,
    default=list(db_symbols),
)

sgd_to_usd_rate = st.sidebar.number_input(
    "SGD to USD FX rate",
    min_value=0.0001,
    value=0.74,
    step=0.0001,
    format="%.4f",
)

trailing_stop_loss_factor = st.sidebar.number_input(
    "Trailing stop loss factor",
    min_value=0.0001,
    value=0.5,
    step=0.01,
    format="%.2f",
)

run_tests_now = st.sidebar.button("Run tests now")
auto_run_tests = st.sidebar.checkbox("Auto-run tests on code change", value=False)
auto_refresh_enabled = st.sidebar.checkbox("Auto-refresh dashboard", value=False)
auto_refresh_seconds = st.sidebar.number_input(
    "Auto-refresh interval (seconds)",
    min_value=1,
    value=5,
    step=1,
)

start_date = st.sidebar.date_input(
    "Start date",
    pd.to_datetime("2024-01-01"),
)

end_date = st.sidebar.date_input(
    "End date",
    pd.to_datetime("today"),
)

if start_date > end_date:
    st.error("Start date must be before or equal to end date.")
    st.stop()

if auto_refresh_enabled:
    if st_autorefresh is None:
        st.warning(
            "Auto-refresh requires 'streamlit-autorefresh'. Install with "
            "'conda install -c conda-forge streamlit-autorefresh' or "
            "'pip install streamlit-autorefresh'."
        )
    else:
        st_autorefresh(interval=int(auto_refresh_seconds * 1000), key="dashboard_autorefresh")

if "last_test_mtime" not in st.session_state:
    st.session_state["last_test_mtime"] = get_latest_python_mtime(PROJECT_ROOT)
if "last_test_ok" not in st.session_state:
    st.session_state["last_test_ok"] = None
if "last_test_output" not in st.session_state:
    st.session_state["last_test_output"] = "No test run yet."
if "last_test_ran_at" not in st.session_state:
    st.session_state["last_test_ran_at"] = None

current_mtime = get_latest_python_mtime(PROJECT_ROOT)
should_run_tests = run_tests_now or (
    auto_run_tests and current_mtime > st.session_state["last_test_mtime"]
)

if should_run_tests:
    with st.spinner("Running test suite..."):
        tests_ok, tests_output = run_test_suite()
    st.session_state["last_test_ok"] = tests_ok
    st.session_state["last_test_output"] = tests_output
    st.session_state["last_test_ran_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["last_test_mtime"] = current_mtime

header_left_col, header_right_col = st.columns([0.78, 0.22])
with header_left_col:
    st.title("Market Data Dashboard")

with header_right_col:
    st.markdown("##### Tests")
    if st.session_state["last_test_ok"] is None:
        st.caption("Not run")
    elif st.session_state["last_test_ok"]:
        st.caption("Passed")
    else:
        st.caption("Failed")
    st.caption(f"Last run: {st.session_state['last_test_ran_at'] or '-'}")
    with st.expander("Details", expanded=False):
        st.code(st.session_state["last_test_output"], language="text")

df = get_prices(
    symbol=symbol,
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
)

st.subheader("Standard deviation of returns")
st.caption("Values shown are latest 25-day rolling standard deviations of daily returns.")

if not symbols_for_table:
    st.info("Select at least one symbol to populate the volatility table.")
else:
    symbol_name_map = get_instrument_symbol_name_map()
    table_rows = []

    for table_symbol in symbols_for_table:
        symbol_prices = get_prices(
            symbol=table_symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        row = {
            "symbol": table_symbol,
            "name": symbol_name_map.get(table_symbol, ""),
            "rolling_25d_std_dev": None,
            "rolling_25d_annualized_std_dev": None,
            "status": "ok",
        }

        try:
            row["rolling_25d_std_dev"] = calculate_return_std_dev(
                symbol_prices,
                rolling_window=25,
            )
            row["rolling_25d_annualized_std_dev"] = calculate_return_std_dev(
                symbol_prices,
                annualize=True,
                rolling_window=25,
            )
        except Exception as exc:
            row["status"] = str(exc)

        table_rows.append(row)

    volatility_df = pd.DataFrame(table_rows)
    st.dataframe(
        volatility_df.style.format(
            {
                "rolling_25d_std_dev": "{:.2%}",
                "rolling_25d_annualized_std_dev": "{:.2%}",
            }
        ),
        use_container_width=True,
    )

st.subheader("Portfolio sizing")
st.caption(
    "Home currency is SGD. Notional risk per instrument = (target risk x capital) / annual risk."
)
st.caption(
    "Assumptions: capital = SGD 3000, target risk = 12%. "
    "FX sizing uses exposure_instrument_ccy = exposure_sgd x SGDUSD. "
    "AAPL/SPY sizing uses shares = (exposure_sgd x SGDUSD) / latest_price."
)
st.caption(
    "Stop loss: gap = annual risk x current price x trailing factor. "
    "For long: stop = entry - gap. For short: stop = entry + gap."
)

if not portfolio_symbols:
    st.info("Select at least one symbol to populate the portfolio sizing table.")
else:
    capital_sgd = 3000.0
    target_risk = 0.12
    portfolio_rows = []

    for portfolio_symbol in portfolio_symbols:
        symbol_prices = get_prices(
            symbol=portfolio_symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        try:
            if symbol_prices.empty:
                raise ValueError("No price data found in selected date range.")

            annual_risk = calculate_return_std_dev(
                prices_df=symbol_prices,
                annualize=True,
                rolling_window=25,
            )

            asset_type = str(symbol_prices["asset_type"].dropna().iloc[-1]).lower()
            latest_price = float(symbol_prices["adjusted_close"].dropna().iloc[-1])
            signal_df_for_symbol = calculate_ma_signal(
                prices_df=symbol_prices,
                price_column="adjusted_close",
                fast_window=16,
                slow_window=64,
            )
            latest_signal_position = str(signal_df_for_symbol["position"].dropna().iloc[-1]).lower()

            sizing_row = build_portfolio_sizing_row(
                symbol=portfolio_symbol,
                asset_type=asset_type,
                annual_instrument_risk=annual_risk,
                capital_home_ccy=capital_sgd,
                target_risk=target_risk,
                fx_rate=sgd_to_usd_rate,
                latest_price=latest_price,
            )
            stop_gap = calculate_stop_loss_gap(
                annual_instrument_risk=annual_risk,
                current_price=latest_price,
                trailing_stop_loss_factor=trailing_stop_loss_factor,
            )

            sizing_row["signal_position"] = latest_signal_position
            sizing_row["entry_price_for_stop"] = latest_price
            sizing_row["stop_loss_gap"] = stop_gap
            sizing_row["trailing_stop_loss_factor"] = trailing_stop_loss_factor

            if latest_signal_position in {"long", "short"}:
                sizing_row["stop_loss_level"] = calculate_stop_loss_level(
                    position=latest_signal_position,
                    initial_entry_price=latest_price,
                    stop_loss_gap=stop_gap,
                )
            else:
                sizing_row["stop_loss_level"] = None

            sizing_row["status"] = "ok"
            portfolio_rows.append(sizing_row)
        except Exception as exc:
            portfolio_rows.append(
                {
                    "symbol": portfolio_symbol,
                    "asset_type": None,
                    "instrument_risk_annual": None,
                    "target_risk": target_risk,
                    "capital_sgd": capital_sgd,
                    "notional_exposure_sgd": None,
                    "fx_exposure_instrument_ccy": None,
                    "latest_price": None,
                    "position_size_shares": None,
                    "signal_position": None,
                    "entry_price_for_stop": None,
                    "stop_loss_gap": None,
                    "trailing_stop_loss_factor": trailing_stop_loss_factor,
                    "stop_loss_level": None,
                    "status": str(exc),
                }
            )

    portfolio_df = build_portfolio_sizing_table(portfolio_rows)
    st.dataframe(
        portfolio_df.style.format(
            {
                "instrument_risk_annual": "{:.2%}",
                "target_risk": "{:.2%}",
                "capital_sgd": "SGD {:.2f}",
                "notional_exposure_sgd": "SGD {:.2f}",
                "fx_exposure_instrument_ccy": "{:.4f}",
                "latest_price": "{:.4f}",
                "position_size_shares": "{:.4f}",
                "entry_price_for_stop": "{:.4f}",
                "stop_loss_gap": "{:.4f}",
                "trailing_stop_loss_factor": "{:.2f}",
                "stop_loss_level": "{:.4f}",
            }
        ),
        use_container_width=True,
    )

st.subheader("MA(16)-MA(64) trading signal")
st.caption(
    "signal_t = MA_16_t - MA_64_t. Positive signal implies long; negative signal implies short."
)

if df.empty:
    st.info("Signal is unavailable because no price data was found for the selected symbol.")
else:
    try:
        signal_df = calculate_ma_signal(
            prices_df=df,
            price_column="adjusted_close",
            fast_window=16,
            slow_window=64,
        )
        signal_column = "signal_ma_16_64"
        ma_fast_column = "ma_16"
        ma_slow_column = "ma_64"

        signal_history = signal_df[["price_date", signal_column]].dropna()

        if signal_history.empty:
            st.warning("Not enough data to compute MA(16)-MA(64) signal.")
        else:
            latest_signal = float(signal_history.iloc[-1][signal_column])
            if latest_signal > 0:
                latest_position = "long"
            elif latest_signal < 0:
                latest_position = "short"
            else:
                latest_position = "flat"

            trend_note = "n/a (need at least 2 signal values)"
            if len(signal_history) >= 2:
                previous_signal = float(signal_history.iloc[-2][signal_column])

                if latest_signal == 0:
                    trend_note = "neutral"
                elif previous_signal == 0:
                    trend_note = "new directional move"
                elif (latest_signal > 0 and previous_signal > 0) or (
                    latest_signal < 0 and previous_signal < 0
                ):
                    if abs(latest_signal) > abs(previous_signal):
                        trend_note = "strengthening"
                    elif abs(latest_signal) < abs(previous_signal):
                        trend_note = "weakening"
                    else:
                        trend_note = "unchanged"
                else:
                    trend_note = "reversal"

            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            metrics_col1.metric("Latest signal", f"{latest_signal:.6f}")
            metrics_col2.metric("Current position", latest_position.upper())
            metrics_col3.metric("Trend vs previous", trend_note)

            st.write("Synchronized view: price + MAs (top), signal (bottom)")
            aligned_df = signal_df[
                ["price_date", "adjusted_close", ma_fast_column, ma_slow_column, signal_column]
            ].dropna()
            st.write("Signal: MA(16) - MA(64)")
            st.line_chart(
                aligned_df.set_index("price_date")[signal_column],
                use_container_width=True,
            )
            st.write("Price with MA(16) and MA(64)")
            st.line_chart(
                aligned_df.set_index("price_date")[
                    ["adjusted_close", ma_fast_column, ma_slow_column]
                ],
                use_container_width=True,
            )
            st.dataframe(signal_history, use_container_width=True)
    except Exception as exc:
        st.warning(str(exc))

st.subheader(f"{symbol} price data")

if df.empty:
    st.warning("No data found.")
else:
    st.write(
        f"Rows: {len(df)} | "
        f"From: {df['price_date'].min().date()} | "
        f"To: {df['price_date'].max().date()}"
    )

    chart_df = df.set_index("price_date")[["close", "adjusted_close"]]

    st.line_chart(chart_df)

    st.subheader("Raw data")
    st.dataframe(df, use_container_width=True)
