from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd

import logging

log = logging.getLogger(__name__)

def soup_url(url):
    log.info("Loading: {}".format(url))
    with urlopen(url) as webobj:
        return BeautifulSoup(webobj.read(), "html.parser")


def try_numeric(val):
    try:
        return pd.to_numeric(val)
    except ValueError:
        return None

def parse_shorthand(num : str):
    num = num.replace(",", "").replace("$", "").replace("%", "e-2")
    num = num.replace("K", "e3").replace("M", "e6").replace("B", "e9")
    return try_numeric(num)