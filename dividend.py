import pandas as pd

from util import soup_url, parse_shorthand

def load_nasdaq_dividends(ticker):
    clean_ticker = ticker.lower().replace("-", ".")
    nasdaq_url = "https://www.nasdaq.com/symbol/{}/dividend-history".format(clean_ticker)
    
    return soup_url(nasdaq_url)

def parse_date(dt : str):
    try:
        return pd.to_datetime(dt)
    except ValueError:
        return None

def parse_nasdaq_dividends(soup):
    table = soup.find("table", id="quotes_content_left_dividendhistoryGrid")
    headers = [th.text.strip() for th in table.thead.find_all("th")]
    data = [[td.text.strip() for td in tr.find_all("td")] for tr in table.tbody.find_all("tr")]
    df = pd.DataFrame(data, columns=headers)
    dt_cols = [col for col in df.columns if "Date" in col]
    df[dt_cols] = df[dt_cols].applymap(parse_date)
    df["Cash Amount"] = df["Cash Amount"].astype(float)
    return df

def load_si_dividends(ticker):
    clean_ticker = ticker.lower().replace(".", "-")
    si_url = "https://www.streetinsider.com/dividend_history.php?q={}".format(clean_ticker)

    return soup_url(si_url)

def parse_si_dividends(soup):
    table = soup.find("table", _class="dividends")
    rows = table.find_all("tr")
    headers = [th.text.strip() for th in rows[0].find_all("th")]
    data = [[td.text.strip() for td in tr.find_all("td")] for tr in rows[1:]]
    df = pd.DataFrame(data, columns=headers)
    dt_cols = [col for col in df.columns if "Date" in col]
    df[dt_cols] = df[dt_cols].applymap(parse_date)
    df["Amount"] = df["Amount"].apply(parse_shorthand)
    df["Change"] = df["Change"].apply(parse_shorthand)
    return df

if __name__ == "__main__":
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="Downloads Nasdaq dividend history")
    parser.add_argument("ticker", help="Symbol to look up")
    parser.add_argument("--source", default="nq", choices=["si", "nq"])
    parser.add_argument("--out", default="dividends.csv", help="Results CSV filename")
    parser.add_argument("--verbose", action="store_true", help="verbose logging")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    if args.source == "si":
        soup = load_si_dividends(args.ticker)
        df = parse_si_dividends(soup)

    elif args.source == "nq":
        soup = load_nasdaq_dividends(args.ticker)
        df = parse_nasdaq_dividends(soup)

    print(df)
    df.to_csv(args.out)