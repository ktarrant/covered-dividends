import pandas as pd

from util import soup_url

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

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Downloads Nasdaq dividend history")
    parser.add_argument("ticker", help="Symbol to look up")
    parser.add_argument("--out", default="dividends.csv", help="Results CSV filename")

    args = parser.parse_args()

    soup = load_nasdaq_dividends(args.ticker)
    df = parse_nasdaq_dividends(soup)
    print(df)
    df.to_csv(args.out)