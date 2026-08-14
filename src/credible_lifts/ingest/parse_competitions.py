"""Parser for competition.htmls crawled from iwrp.net.

Run from the repo root: uv run python -m credible_lifts.ingest.parse_competitions
"""

import csv
from pathlib import Path

from bs4 import BeautifulSoup

COMP = Path("data/raw/iwrp/pages/competitions")
PARS = Path("data/parsed")

def comp_description(soup):
    h1 = soup.find("h1")
    competition_name = h1.get_text(" ", strip=True)
    date = h1.find_next("div").get_text(" ", strip=True).split("·")[0].strip()
    return competition_name, date

def result_table(soup):
    for t in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True) for th in t.select("tr th")]
        if "Athlete" in headers:            
            yield t, headers

def cell(name, row, idx):
    i = idx.get(name)
    return row[i] if i is not None and i < len(row) else None

def num(text):
    text = (text or "").strip()
    if text in ("", "—", "--"):
        return None
    try: 
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return "?" + text

def text_or_none(td):
    if td is None:
        return td
    return td.get_text(" ", strip=True)

def num_of(td):
    if td is None:
        return td
    return num(td.get_text(" ", strip=True))

def athlete_id(tr):
    a = tr.select_one('a[href*="/public/zawodnik/"]')
    if a is None:
        return a
    return num(a.get_attribute_list("href")[0].rsplit("/", 1)[1].split("-")[0])

def attempt(td):
    if td is None:
        return None
    v = num(td.get_text(strip=True))
    if isinstance(v, (int, float)) and "neg" in (td.get("class") or []):
        return -v                        # missed lift -> negative
    return v

if __name__ == "__main__":
    rows = []
    rows_seen = 0
    rows_written = 0
    quarantined = 0
    for html in sorted(COMP.iterdir(), key=lambda k:int(k.stem.split("_")[1])):
        competition_id = int(html.stem.split("_")[1])
        soup = BeautifulSoup(html.read_text(encoding="utf-8"), "html.parser")
        competition_name, date = comp_description(soup)
        for table, headers in result_table(soup):
            idx = {header: i for i, header in enumerate(headers)}
            category = table.find_previous(["h2"]).get_text(strip=True)
            if category.startswith("K "):
                category = "W " + category[2:]
            if "Country" not in idx and "Club" not in idx:
                category = "Team"
            # walk rows
            for tr in table.select("tr"):
                tds = tr.find_all("td")
                if not tds:
                    continue
                rank_txt = cell("#", tds, idx).get_text(strip=True) if cell("#", tds, idx) else ""
                row = {
                    "competition_id": competition_id, "competition_name": competition_name,"date": date, "category": category,
                    "rank": num(rank_txt), 
                    "athlete_id": athlete_id(tr), "athlete_name": text_or_none(cell("Athlete", tds, idx)), 
                    "gender": "M" if category.startswith("M ") else "W" if category.startswith("W ") else None,
                    "country": text_or_none(cell("Country", tds, idx)), 
                    "club": text_or_none(cell("Club", tds, idx)), 
                    "bodyweight": num_of(cell("Weight", tds, idx)), 
                    "sn1": attempt(cell("Sn1", tds, idx)), 
                    "sn2": attempt(cell("Sn2", tds, idx)),
                    "sn3": attempt(cell("Sn3", tds, idx)),
                    "best_snatch": num_of(cell("MAX Sn", tds, idx)),
                    "cj1": attempt(cell("CJ1", tds, idx)),  
                    "cj2": attempt(cell("CJ2", tds, idx)),   
                    "cj3": attempt(cell("CJ3", tds, idx)),
                    "best_cj": num_of(cell("MAX CJ", tds, idx)),  
                    "total": num_of(cell("Total", tds, idx)),
                    "sinclair": num_of(cell("Sinclair", tds, idx))
                }
                rows_seen += 1
                if row["athlete_id"] is None or any(isinstance(v, str) and v.startswith("?") for v in row.values()):
                    quarantined += 1
                    continue
                rows.append(row)
                rows_written += 1

    # Write csv
    with open(PARS / "competitions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    athlete_ids = list({row["athlete_id"] for row in rows})

    print(f"""
    Summary: 
    - rows seen: {rows_seen}
    - rows written: {rows_written}
    - quarantined: {quarantined}
    - reconciles: {rows_seen == rows_written + quarantined}
    - distinct athletes: {len(athlete_ids)}
    """)
