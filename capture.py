import datetime
import pandas as pd
import logging

from screener import load_finviz_screener, parse_finviz_screener
from dividend import load_nasdaq_dividends, parse_nasdaq_dividends
from contracts import (
    load_nasdaq_options,
    parse_expirations,
    ExpirationError,
    find_expirations_after,
    find_expirations_before,
)

log = logging.getLogger(__name__)

def find_otm_options(exp_df, exp_date, price, option="Call", after=True, above=True, day_offset=0):
    comp_offset = day_offset if after else -day_offset
    comp_date = exp_date + datetime.timedelta(days=comp_offset)

    if after:
        chain_df = find_expirations_after(exp_df, comp_date, option=option)
    else:
        chain_df = find_expirations_before(exp_df, comp_date, option=option)

    if above:
        otm = chain_df[chain_df.Strike >= price]
    else:
        otm = chain_df[chain_df.Strike <= price]
    log.debug("Found {} OTM {}s".format(len(otm.index), option))

    return otm

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
    try:
        otm_puts = find_otm_options(exp_df, next_div_date, max_put_strike, option="Put", after=False, above=False, day_offset=days_before_div)
        if len(otm_puts.index) > 0:
            best_put_row = otm_puts.loc[otm_puts["Put Open"].argmax()].rename(
                index={"Strike": "Put Strike"})
            log.info("Best put row:\n{}".format(best_put_row))
        else:
            log.error("No OTM puts found!")
            best_put_row = pd.Series()
    except ExpirationError as e:
        log.error(e)
        best_put_row = pd.Series()

    # find calls expiring after the dividend
    try:
        otm_calls = find_otm_options(exp_df, next_div_date, min_call_strike, day_offset=days_after_div)
        if len(otm_calls.index) > 0:
            best_call_row = otm_calls.loc[otm_calls["Call Open"].argmax()].rename(
                index={"Strike": "Call Strike"})
            log.info("Best call row:\n{}".format(best_call_row))
        else:
            log.error("No OTM calls found!")
            best_call_row = pd.Series()
    except ExpirationError as e:
        log.error(e)
        best_call_row = pd.Series()

    # combined the two and return
    df = pd.concat([best_put_row, best_call_row])
    df["Ex-Div Date (est)"] = next_div_date.date()
    df["Div Amount (est)"] = div_cash
    df["Dividend Period"] = div_period.days
    return df

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