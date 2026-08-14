"""Parser for athlete.htmls crawled from iwrp.net.

Run from the repo root: uv run python -m credible_lifts.ingest.parse_athletes
"""

import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

ATHL = Path("data/raw/iwrp/pages/athletes")
PARS = Path("data/parsed")

def athlete_name(soup):
    div = soup.find("div", class_="zawodnik-header")
    return div.select_one("h1.zawody-tytul").get_text(" ", strip=True)

def athlete_description(soup):
    div = soup.find("div", class_="zawodnik-header")
    description = div.select("div.zawody-meta")
    headers = [meta_data.get_text(" ", strip=True).split(":")[0] for meta_data in description]
    return description, headers

def cell(name, description, idx):
    i = idx.get(name)
    return description[i] if i is not None and i < len(description) else None

def text_or_none(cell):
    if cell is None:
        return cell
    return cell.get_text(" ", strip=True)

if __name__ == "__main__":
    rows = []
    rows_seen = 0
    rows_written = 0
    quarantined = 0
    for html in sorted(ATHL.iterdir(), key=lambda k:int(k.stem.split("_")[1])):
        athlete_id = int(html.stem.split("_")[1])
        soup = BeautifulSoup(html.read_text(encoding="utf-8"), "html.parser")
        name = athlete_name(soup)
        description, headers = athlete_description(soup)
        idx = {header: i for i,header in enumerate(headers)}
        birthdate_gender = text_or_none(cell("Date of birth", description, idx))
        m = re.match(r"Date of birth:\s*([\d-]+)\s+'?([MK])'?", birthdate_gender) if birthdate_gender else None
        if m:
            birthdate, gender = m.group(1), m.group(2)
            if gender == "K":
                gender = "W"
        else:
            birthdate = gender = None
        nation_raw = text_or_none(cell("Nation", description, idx))
        nation = nation_raw.split(":")[1].strip() if nation_raw else None
        row = {
            "athlete_id": athlete_id, "athlete_name": name,
            "birthdate": birthdate, "gender": gender, "nation": nation
        }
        rows_seen += 1
        if None in row.values():
            quarantined += 1
            continue
        rows.append(row)
        rows_written += 1

    # Write csv
    with open(PARS / "athletes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"""
    Summary: 
    - rows seen: {rows_seen}
    - rows written: {rows_written}
    - quarantined: {quarantined}
    - reconciles: {rows_seen == rows_written + quarantined}
    """)
