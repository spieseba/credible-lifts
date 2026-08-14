"""Build plan for crawling iwrp.net (run per page type; output is a worklist for crawl.py).

Run from the repo root: uv run python -m credible_lifts.ingest.build_plan
"""

import json
from pathlib import Path

from bs4 import BeautifulSoup

IWRP = Path("data/raw/iwrp")
PAGE_TYPE = "athlete" # "athlete" or "competition" - keep in sync with crawl.py
PAGE = {"athlete": "zawodnik", "competition": "zawody"}[PAGE_TYPE]

def get_locs(xml_path):
    soup = BeautifulSoup(xml_path.read_text(encoding="utf-8"), "xml")
    return [el.get_text() for el in soup.select("loc")]

if __name__ == "__main__":
    children = get_locs(IWRP / "sitemap.xml")
    urls = [url for child in children for url in get_locs(IWRP / child.rsplit("/",1)[1]) if f"/public/{PAGE}/" in url] 
    print(f"Found {len(urls)} urls for {PAGE_TYPE}s")
    rows = [{f"{PAGE_TYPE}_id": int(url.rsplit("/", 1)[1].split("-",1)[0]), "url": url} for url in urls]
    with open(IWRP / f"plan_{PAGE_TYPE}s.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)