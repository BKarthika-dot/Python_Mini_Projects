"""
Web-fetch and text-extraction module (accept a job posting
URL, fetch and parse its content).

This is the primary input path for the system: given a URL, go get the page,
strip out navigation/boilerplate/ads, and return the job-relevant text
(title + main content) for the rest of the pipeline to analyze.

Many job boards (Indeed, LinkedIn, etc.) run bot-detection that blocks plain
`requests` calls with a 403, even with a normal-looking User-Agent. This
module reduces how often that happens by using a persistent session with a
full set of realistic browser headers, warming the session up with a GET to
the site's homepage first (so it picks up cookies the way a real browser
visit would), and retrying with backoff. If the site still blocks it, a
clear, actionable ValueError is raised instead of a raw request exception --
callers (test_cli.py, the API, module_demo.py) already surface ValueError
messages directly to the user.
"""
import random
import time
from typing import Optional
from urllib.parse import urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup

_TIMEOUT = 15
_MIN_USABLE_CHARS = 40
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 1.5

# A small rotation of realistic, current desktop-browser User-Agent strings.
# Rotating (instead of one fixed string) avoids looking like a static bot
# signature on a retry.
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]


def _build_headers(referer: Optional[str] = None) -> dict:
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin" if referer else "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"'{url}' is not a valid http(s) URL.")


def _homepage_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _warm_up_session(session: requests.Session, url: str) -> None:
    """Visit the site's homepage first so the session picks up cookies,
    the way a real browser visit would -- some sites reject requests that
    go straight to a deep link with no prior visit/cookies at all."""
    try:
        session.get(_homepage_url(url), headers=_build_headers(), timeout=_TIMEOUT)
    except requests.exceptions.RequestException:
        pass  # best-effort only; the real request below still gets attempted


def _fetch_html(url: str) -> str:
    """Fetch raw HTML for a URL, raising a clear ValueError on any failure."""
    _validate_url(url)

    session = requests.Session()
    _warm_up_session(session, url)

    last_status = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            resp = session.get(
                url,
                headers=_build_headers(referer=_homepage_url(url)),
                timeout=_TIMEOUT,
                allow_redirects=True,
            )
        except requests.exceptions.Timeout as e:
            if attempt == _MAX_ATTEMPTS:
                raise ValueError(f"Timed out while fetching the job posting URL: {url}") from e
        except requests.exceptions.SSLError as e:
            raise ValueError(f"SSL/certificate error while fetching URL: {url}") from e
        except requests.exceptions.ConnectionError as e:
            if attempt == _MAX_ATTEMPTS:
                raise ValueError(f"Could not connect to the job posting URL: {url}") from e
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch the job posting URL: {url} ({e})") from e
        else:
            last_status = resp.status_code

            if resp.status_code == 404:
                raise ValueError(f"The job posting URL returned 404 Not Found: {url}")

            if resp.status_code in (403, 429):
                # Likely bot-detection. Retry with backoff + a fresh UA
                # before giving up.
                if attempt < _MAX_ATTEMPTS:
                    time.sleep(_BACKOFF_SECONDS * attempt)
                    continue
                raise ValueError(
                    f"This site is blocking automated access (HTTP {resp.status_code}): {url}\n"
                    "Many job boards (e.g. Indeed, LinkedIn) actively block scraping. "
                    "Copy the job posting text and submit it directly instead, "
                    "e.g. `python test_cli.py --text \"<pasted job description>\"`."
                )

            if resp.status_code in (401,):
                raise ValueError(f"Access to the job posting URL was denied (HTTP {resp.status_code}): {url}")

            if resp.status_code >= 500:
                if attempt < _MAX_ATTEMPTS:
                    time.sleep(_BACKOFF_SECONDS * attempt)
                    continue
                raise ValueError(f"The job posting site returned a server error (HTTP {resp.status_code}): {url}")

            if resp.status_code >= 400:
                raise ValueError(f"The job posting URL returned an error (HTTP {resp.status_code}): {url}")

            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                raise ValueError(
                    f"The URL did not return an HTML page (Content-Type: {content_type or 'unknown'}): {url}"
                )

            resp.encoding = resp.encoding or "utf-8"
            return resp.text

    # Should not normally be reached, but guard just in case.
    raise ValueError(f"Failed to fetch the job posting URL after {_MAX_ATTEMPTS} attempts "
                      f"(last status: {last_status}): {url}")


def _extract_title(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return " ".join(soup.title.string.split())
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return " ".join(og_title["content"].split())
    h1 = soup.find("h1")
    if h1:
        return " ".join(h1.get_text(separator=" ").split())
    return None


def _extract_main_content_bs4(html: str) -> str:
    """Fallback extractor: strip obvious boilerplate, return remaining visible text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form", "aside"]):
        tag.decompose()
    # Prefer common job-posting/article containers if present.
    candidates = soup.select("article, main, [class*='job'], [class*='posting'], [id*='job']")
    if candidates:
        text = " ".join(c.get_text(separator=" ") for c in candidates)
    else:
        text = soup.get_text(separator=" ")
    return " ".join(text.split())


def fetch_job_posting(url: str) -> str:
    """
    Fetch a job posting URL and return its extracted text (title + main
    content), stripped of navigation/boilerplate, ready for classification.
    """
    html = _fetch_html(url)

    title = _extract_title(html)

    main_text = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    main_text = " ".join(main_text.split())

    if len(main_text) < _MIN_USABLE_CHARS:
        # trafilatura came back empty/too short (common on heavily scripted
        # or unusually structured pages) -- fall back to a simpler BS4 pass.
        main_text = _extract_main_content_bs4(html)

    if len(main_text) < _MIN_USABLE_CHARS:
        raise ValueError(
            f"Could not extract readable job posting text from this URL: {url} "
            "(the page may require JavaScript to render, or may not be a job posting). "
            "Try pasting the job description text directly instead."
        )

    combined = f"{title}. {main_text}" if title and title not in main_text[:len(title) + 5] else main_text
    return combined