import datetime
from collections import OrderedDict
import pandas as pd

from util import soup_url, try_numeric, parse_shorthand

url_filter_options = OrderedDict([
    ("cap_mega", "Mega Market Cap"),
    ("fa_payoutratio_pos", "Positive Payout Ratio"),
    ("idk_sp500", "S&P500 Member"),
])
url_base = "https://finviz.com/screener.ashx?"
pct_columns = ["Change", "Dividend", "Gross M", "Oper M", "Profit M", "ROA", "ROE", "ROI"]

def load_finviz_screener(filter_options=list(url_filter_options.keys())):
    url_params = OrderedDict([
        ("v", "161"),
        ("f", ",".join(filter_options)),
        ("ft", "4"),
        ("o", "-dividendyield"),
    ])
    screener_url = url_base + "&".join(["{}={}".format(k, url_params[k]) for k in url_params])
    return soup_url(screener_url)

def estimate_year(dt : datetime.date, cutoff_days=182):
    today = datetime.date.today()
    est = datetime.date(year=today.year, month=dt.month, day=dt.day)
    if est > today:
        return est
    else:
        if (today - est).days > cutoff_days:
            return est + datetime.timedelta(days=365)
        else:
            return est

def parse_earnings(ed : str):
    ed_date_raw, ed_time_raw = ed.split("/")
    ed_date = datetime.datetime.strptime(ed_date_raw, "%b %d")
    ed_date = estimate_year(ed_date)
    return ed_date
    
def parse_finviz_screener(soup):
    content = soup.find('div', {'id': 'screener-content'})
    subtable = content.find('table')
    subrows = subtable.findAll('tr', recursive=False)
    contentrow = subrows[3]
    contenttable = contentrow.find('table')
    contentrows = contenttable.findAll('tr')
    headers = [td.text for td in contentrows[0].findAll('td', recursive=False)]
    df = pd.DataFrame([[td.text for td in contentrow.findAll('td')]
        for contentrow in contentrows[1:]],
        columns=headers).set_index("Ticker")
    df["Earnings"] = df["Earnings"].apply(parse_earnings)
    numeric_cols = [col for col in df.columns if col not in "Earnings"]
    df[numeric_cols] = df[numeric_cols].applymap(parse_shorthand)
    df = df.rename(index=str, columns={c: c+" %" for c in pct_columns})
    return df

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Downloads Finviz screener results")
    parser.add_argument("--out", default="screener.csv", help="Results CSV filename")

    for ufo in url_filter_options:
        parser.add_argument("--"+ufo, action="store_true", help="Enable filter: {}".format(
            url_filter_options[ufo]))

    args = parser.parse_args()

    ufos = [ufo for ufo in url_filter_options if (ufo in args) and getattr(args, ufo)]
    soup = load_finviz_screener(ufos)
    df = parse_finviz_screener(soup)
    print(df)
    df.to_csv(args.out)