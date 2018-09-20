import datetime
import pandas as pd
from util import soup_url

def load_nasdaq_options(ticker):
    clean_ticker = ticker.replace("-", ".").lower()
    url = "https://www.nasdaq.com/symbol/{}/option-chain".format(clean_ticker)
    
    return soup_url(url)

def parse_short_date(dt : str, day=1):
    dt = datetime.datetime.strptime(dt, "%b %y")
    dt = datetime.date(year=dt.year, month=dt.month, day=day)
    return dt
    
def parse_expirations(soup):
    chain_dates = soup.find("div", id="OptionsChain-dates")
    
    headers = ["Expiration Month", "Link"]
    data = [[parse_short_date(a.text.strip()), a.attrs["href"]]
        for a in chain_dates.find_all("a")
        if a.text.strip() not in ["Near Term", "All"]]
    return pd.DataFrame(data, columns=headers)
    # for a in chain_dates.find_all("a"):
    #     s = a.text
    #     try:
    #         yield (dt, a.attrs["href"])
    #     except ValueError:
    #         pass

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Downloads Nasdaq options chain data")
    parser.add_argument("ticker", help="Symbol to look up")

    args = parser.parse_args()

    soup = load_nasdaq_options(args.ticker)
    df = parse_expirations(soup)
    print(df)