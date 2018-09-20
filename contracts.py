import datetime
import pandas as pd
import logging

from util import soup_url, try_numeric

log = logging.getLogger(__name__)

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

def parse_chain(soup):
    chain = soup.find("div", {"class": "OptionsChain-chart"})
    table = chain.table
    header_links = table.find_all("th")
    columns = [link.text.split()[0].strip() for link in header_links]
    root_index = columns.index("Root")
    columns[0] = "Call Expiration"
    for i in range(1, root_index):
        columns[i] = "Call " + columns[i]
    columns[root_index + 2] = "Put Expiration"
    for i in range(root_index + 3, len(columns)):
        columns[i] = "Put " + columns[i]

    data = [[td.text.strip() for td in row.find_all("td")] for row in table.find_all("tr")[1:]]
    
    df = pd.DataFrame(data, columns=columns)
    dt_cols = ["Call Expiration", "Put Expiration"]
    df[dt_cols] = df[dt_cols].apply(pd.to_datetime, axis=1)
    num_cols = [col for col in df.columns if "Expiration" not in col]
    df[num_cols] = df[num_cols].applymap(try_numeric)
    df = df.drop("Root", axis=1).set_index("Strike")
    return df

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Downloads Nasdaq options chain data")
    parser.add_argument("ticker", help="Symbol to look up")
    parser.add_argument("--after", default=None, help="Pick an expiration after this date")

    args = parser.parse_args()

    soup = load_nasdaq_options(args.ticker)
    exp_df = parse_expirations(soup)
    print(exp_df)
    if args.after:
        raise NotImplementedError("--after")

    else:
        chain_df = parse_chain(soup)
        print(chain_df)