import logging

from screener import load_finviz_screener, parse_finviz_screener
from capture import find_wheel_options

log = logging.getLogger(__name__)

def add_capture_options(screener_df, days_before_div, days_after_div, put_downside, call_upside):
    for ticker in screener_df.index:
        price = screener_df.loc[ticker, "Price"]
        put_price = (1 - args.put_downside / 100.0) * price
        call_price = (1 + args.call_upside / 100.0) * price

        wheel_df = find_wheel_options(ticker,
            max_put_strike=put_price,
            min_call_strike=call_price,
            days_before_div=args.days_before_div,
            days_after_div=args.days_after_div)

        for i in wheel_df.index:
            screener_df.loc[ticker, i] = wheel_df.loc[i]

if __name__ == "__main__":
    import datetime
    import argparse
    from collections import OrderedDict

    filters = OrderedDict([
        ("blue-chips", ["cap_mega", "fa_payoutratio_pos", "idk_sp500"]),
    ])

    parser = argparse.ArgumentParser(description="Finds a put option and call option for wheeling")
    parser.add_argument("--screener", default="blue-chips", choices=list(filters.keys()))
    parser.add_argument("--days_before_div", default=10, type=int,
        help="Min days before dividend that the put option should expire")
    parser.add_argument("--days_after_div", default=20, type=int,
        help="Min days after dividend that the call option should expire")
    parser.add_argument("--put_downside", default=1, type=float,
        help="Put strike below this percent (/100) below current price")
    parser.add_argument("--call_upside", default=5, type=float,
        help="Call strike above this percent (/100) above current price")
    parser.add_argument("--out", default="{today}_{screener}.csv", help="Result CSV format")
    parser.add_argument("--verbose", action="store_true", help="verbose logging")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    screener_soup = load_finviz_screener(filter_options=filters[args.screener])
    screener_df = parse_finviz_screener(screener_soup)
    log.info("Screener results:\n{}".format(screener_df))

    add_capture_options(screener_df,
        args.days_before_div, args.days_after_div,
        args.put_downside, args.call_upside)

    print(screener_df)
    fn = args.out.format(today=datetime.date.today(), screener=args.screener)
    log.info("Saving file: {}".format(fn))
    screener_df.to_csv(fn)