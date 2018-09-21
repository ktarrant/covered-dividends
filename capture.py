import datetime
import pandas as pd
import logging

from screener import load_finviz_screener, parse_finviz_screener
from dividend import load_nasdaq_dividends, parse_nasdaq_dividends
from contracts import (
    load_nasdaq_options,
    parse_expirations,
    find_expirations_after,
    find_expirations_before,
)

log = logging.getLogger(__name__)

def find_wheel_options(ticker, max_put_strike, min_call_strike, days_before_div=10, days_after_div=20):
    # load the dividend history from nasdaq
    div_soup = load_nasdaq_dividends(ticker)
    div_df = parse_nasdaq_dividends(div_soup)

    # compute the dividend credit and the period (i.e. quarterly vs yearly)
    div_cash = div_df["Cash Amount"].iloc[0]
    div_dates = div_df["Ex/Eff Date"]
    latest_div_date = div_dates.iloc[0]
    div_period = latest_div_date - div_dates.iloc[1]
    today = datetime.date.today()
    if today > latest_div_date.date():
        # the latest date listed is in the past, attempt to estimate the next one
        next_div_date = latest_div_date + div_period
    else:
        next_div_date = latest_div_date
    log.info("Next expected dividend: ${} on {}".format(div_cash, next_div_date))

    # load the expirations for this ticker
    exp_soup = load_nasdaq_options(ticker)
    exp_df = parse_expirations(exp_soup)
    log.debug("Found expiration months:\n{}".format(exp_df["Expiration Month"]))

    # find puts expiring before the dividend
    before_date = next_div_date - datetime.timedelta(days=days_before_div)
    put_chain_df = find_expirations_before(exp_df, before_date, option="Put")
    otm_puts = put_chain_df[put_chain_df.Strike <= max_put_strike]
    log.debug("Found {} OTM puts".format(len(otm_puts.index)))
    if len(otm_puts.index) > 0:
        best_put_row = otm_puts.loc[otm_puts["Put Open"].argmax()].rename(
            index={"Strike": "Put Strike"})
        log.info("Best put row:\n{}".format(best_put_row))
    else:
        log.error("No OTM puts found!")
        best_put_row = pd.Series()

    # find calls expiring after the dividend
    after_date = next_div_date + datetime.timedelta(days=days_after_div)
    call_chain_df = find_expirations_after(exp_df, after_date.date(), option="Call")
    otm_calls = call_chain_df[call_chain_df.Strike >= min_call_strike]
    log.debug("Found {} OTM calls".format(len(otm_calls.index)))
    if len(otm_calls.index) > 0:
        best_call_row = otm_calls.loc[otm_calls["Call Open"].argmax()].rename(
            index={"Strike": "Call Strike"})
        log.info("Best call row:\n{}".format(best_call_row))
    else:
        log.error("No OTM calls found!")
        best_call_row = pd.Series()

    # combined the two and return
    return pd.concat([best_put_row, best_call_row])

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Finds a put option and call option for wheeling")
    parser.add_argument("ticker", help="Symbol to look up")
    parser.add_argument("price", help="Straddle price", type=float)
    parser.add_argument("--days_before_div", default=10, type=int,
        help="Min days before dividend that the put option should expire")
    parser.add_argument("--days_after_div", default=20, type=int,
        help="Min days after dividend that the call option should expire")
    parser.add_argument("--verbose", action="store_true", help="verbose logging")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    df = find_wheel_options(args.ticker,
        max_put_strike=args.price,
        min_call_strike=args.price,
        days_before_div=args.days_before_div,
        days_after_div=args.days_after_div)
    print(df)