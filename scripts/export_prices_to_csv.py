import argparse
from pathlib import Path

from query_prices import get_prices


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export prices from SQLite database to a CSV file."
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Instrument symbol in DB, e.g. AAPL",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Optional end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--source-name",
        default="yahoo",
        help="Data source name",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output CSV file path",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    df = get_prices(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        source_name=args.source_name,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"Exported {len(df)} rows to {output_path}")


if __name__ == "__main__":
    main()
