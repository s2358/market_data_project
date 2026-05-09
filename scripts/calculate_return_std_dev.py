import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.returns import calculate_return_std_dev
from query_prices import get_prices


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate latest rolling standard deviation of returns for a symbol."
    )
    parser.add_argument("--symbol", required=True, help="Instrument symbol in DB, e.g. AAPL")
    parser.add_argument("--start-date", default=None, help="Optional start date YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Optional end date YYYY-MM-DD")
    parser.add_argument("--source-name", default="yahoo", help="Data source name")
    parser.add_argument(
        "--price-column",
        default="adjusted_close",
        choices=["close", "adjusted_close"],
        help="Price column to use for return calculation",
    )
    parser.add_argument(
        "--annualized",
        action="store_true",
        help="Return annualized standard deviation using trading-day scaling",
    )
    parser.add_argument(
        "--periods-per-year",
        type=int,
        default=252,
        help="Periods per year for annualization",
    )
    parser.add_argument(
        "--rolling-window",
        type=int,
        default=25,
        help="Rolling window size in days",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    prices = get_prices(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        source_name=args.source_name,
    )

    std_dev = calculate_return_std_dev(
        prices_df=prices,
        price_column=args.price_column,
        annualize=args.annualized,
        periods_per_year=args.periods_per_year,
        rolling_window=args.rolling_window,
    )

    label = (
        f"annualized {args.rolling_window}-day rolling std dev"
        if args.annualized
        else f"{args.rolling_window}-day rolling std dev"
    )
    print(
        f"{args.symbol} {label} of daily simple returns "
        f"({args.price_column}): {std_dev:.6f}"
    )


if __name__ == "__main__":
    main()
