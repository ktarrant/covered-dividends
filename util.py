from urllib.request import urlopen
from bs4 import BeautifulSoup
import logging

log = logging.getLogger(__name__)

def soup_url(url):
    log.info("Loading: {}".format(url))
    with urlopen(url) as webobj:
        return BeautifulSoup(webobj.read(), "html.parser")