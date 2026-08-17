"""Build plan for crawling iwrp.net (run per page type; output is a worklist for crawl.py).

Run from the repo root: uv run python -m credible_lifts.ingest.build_plan
"""

import json
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

IWRP = Path("data/raw/iwrp")
PARSED = Path("data/parsed")
PAGE_TYPE = "athlete" # "athlete" or "competition" - keep in sync with crawl.py
PAGE = {"athlete": "zawodnik", "competition": "zawody"}[PAGE_TYPE]
PLAN = IWRP / f"plan_{PAGE_TYPE}s.json"

def get_locs(xml_path):
    soup = BeautifulSoup(xml_path.read_text(encoding="utf-8"), "xml")
    return [el.get_text() for el in soup.select("loc")]

def get_aids_to_fetch(comp_csv):
    df = pd.read_csv(comp_csv)
    # get aids with 3 or more results
    df_valid_total = df[df['total'] > 0]
    result_counts = df_valid_total['athlete_id'].value_counts()
    athlete_ids_to_keep = result_counts[result_counts >=3]
    # filter aids of df
    df_fetch = df[df['athlete_id'].isin(athlete_ids_to_keep.index)]
    return df_fetch.sort_values(by="sinclair", ascending=False).drop_duplicates(subset='athlete_id', keep='first')['athlete_id']


if __name__ == "__main__":

    # Get all rows in sitemap.xml
    children = get_locs(IWRP / "sitemap.xml")
    urls = [url for child in children for url in get_locs(IWRP / child.rsplit("/",1)[1]) if f"/public/{PAGE}/" in url] 
    print(f"Found {len(urls)} urls for {PAGE_TYPE}s")
    rows = [{f"{PAGE_TYPE}_id": int(url.rsplit("/", 1)[1].split("-",1)[0]), "url": url} for url in urls]

    # Only fetch athlete pages with 3 or more results
    if PAGE_TYPE == "athlete":
        aids_to_fetch = get_aids_to_fetch(PARSED / "competitions.csv")
        print(f"Found {len(aids_to_fetch)} athletes with 3 or more results -> restrict plan to those athlete pages")
        lookup = {entry['athlete_id']: i for i, entry in enumerate(rows)}
        rows = [rows[lookup[aid]] for aid in aids_to_fetch]

    with open(PLAN, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)