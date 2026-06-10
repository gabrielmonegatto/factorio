import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "https://www.stempublishing.com/"


def fetch_page(url: str) -> str:
    """Download a page and return its HTML as text."""
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_links(html: str) -> list[dict]:
    """Parse the HTML and return a list of dicts with title and url.
    For now we just pull all <a> tags that look like a book/article link.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for a in soup.select("a[href]"):
        href = a["href"]
        # ignore navigation links, keep only absolute or relative that point to content
        if href.startswith("/books") or href.startswith("/articles"):
            title = a.get_text(strip=True) or href
            full_url = href if href.startswith("http") else f"{BASE_URL.rstrip('/')}{href}"
            results.append({"title": title, "url": full_url})
    return results


def crawl_site(start_url: str = BASE_URL) -> list[dict]:
    """Simple crawl – fetch the start page, extract links, then fetch each linked page for deeper links.
    This is a minimal example; production would need pagination, rate‑limits, etc.
    """
    visited = set()
    to_visit = [start_url]
    all_items = []
    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            html = fetch_page(url)
            links = extract_links(html)
            all_items.extend(links)
            # schedule next level links (only one depth for demo)
            for link in links:
                if link["url"] not in visited and len(visited) < 50:
                    to_visit.append(link["url"])
        except Exception as e:
            print(f"[spider_worker] erro ao buscar {url}: {e}")
    return all_items

if __name__ == "__main__":
    items = crawl_site()
    print(json.dumps(items, ensure_ascii=False, indent=2))
