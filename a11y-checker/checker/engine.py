"""
engine.py

Top-level entry points for running the accessibility checks:
- check_html(html_string, source_label) -> Report
- check_url(url) -> Report  (fetches the page first)
"""

import requests
from bs4 import BeautifulSoup

from .models import Report
from .rules import ALL_CHECKS

DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_USER_AGENT = "A11yChecker/1.0 (+https://github.com/Calplexable/a11y-checker)"


def check_html(html: str, source: str = "<pasted HTML>") -> Report:
    """
    Run every registered accessibility check against a raw HTML string
    and return a populated Report.
    """
    soup = BeautifulSoup(html, "lxml")
    report = Report(source=source)

    for check_fn in ALL_CHECKS:
        for issue in check_fn(soup):
            report.add(issue)

    return report


def check_url(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Report:
    """
    Fetch a URL and run the accessibility checks against its HTML.
    Raises requests.RequestException on network/HTTP errors so callers
    (CLI/web) can decide how to present the failure.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return check_html(response.text, source=url)
