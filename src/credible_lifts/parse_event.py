from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd


# parse card
FIELDS_SNATCHJERK = ["rank", "name", "nation", "born", "bodyweight", "group", "attempt-1", "attempt-2", "attempt-3", "total"]
FIELDS_TOTAL = ["rank", "name", "nation", "born", "bodyweight", "group", "snatch", "cleanjerk", "total"]

def to_int(text):
    return None if text == "---" else int(text)


# parse "Snatch" and "Clean&Jerk" cards
def parse_snatchjerk_card(card):
    values = []
    for p in card.select("p"):
        text = " ".join(p.get_text(" ").split())
        values.append("---" if p.select_one("strike") else text.split(":", 1)[-1].strip())
    row = dict(zip(FIELDS_SNATCHJERK, values))
    for field in ["rank", "attempt-1", "attempt-2", "attempt-3", "total"]:
        row[field] = to_int(row[field])
    row["bodyweight"] = float(row["bodyweight"])
    return row

# pase "Total" cards
def parse_total_card(card):
    texts = [" ".join(p.get_text(" ").split()) for p in card.select("p")]
    values = [t.split(":", 1)[-1].strip() for t in texts]
    row = dict(zip(FIELDS_TOTAL, values))
    for field in ["rank", "snatch", "cleanjerk", "total"]:
        row[field] = to_int(row[field])
    row["bodyweight"] = float(row["bodyweight"])
    row["bio_url"] = "".join(card.select_one("a.title").get("href").split())
    return row


def parse_tab(soup, tab_id):
    tab = soup.select_one(f"#{tab_id}")

    titles = [t for t in tab.select("div.results__title") if t.select_one("p")]
    bodyweight_classes = [bwc.select_one("h3").get_text(" ", strip=True) for bwc in tab.select("div.results__title") if bwc.select_one("h3") for _ in range(3)]
    blocks = tab.select("div.cards") 

    rows_snatch, rows_cj, rows_total = [], [], []
    for title, block, bodyweight_class in zip(titles, blocks, bodyweight_classes, strict=True):
        category = title.select_one("p").get_text(" ", strip=True)
        if category not in ["Snatch", "Clean&Jerk", "Total"]:
            raise ValueError(f"Unknown category {category}!")
        for card in block.select("div.card:not(.card__legend)"):
            row = parse_snatchjerk_card(card) if category in ["Snatch", "Clean&Jerk"] else parse_total_card(card)
            row["bodyweight_class"] = bodyweight_class
            if category == "Snatch":
                rows_snatch.append(row)
            elif category == "Clean&Jerk":
                rows_cj.append(row)
            elif category == "Total":
                rows_total.append(row)
    return rows_snatch, rows_cj, rows_total


if __name__ == "__main__":

    html = (Path(__file__).parents[2] / "data" / "raw" / "event_673.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    rows_snatch_men, rows_cj_men, rows_total_men = parse_tab(soup, "men_snatchjerk")
    rows_snatch_women, rows_cj_women, rows_total_women = parse_tab(soup, "women_snatchjerk")

    df_total = pd.DataFrame(rows_total_men + rows_total_women)
    print(df_total.shape)
    print(df_total[df_total["bodyweight_class"] == "110 kg Men"])
    print(df_total[df_total["name"]=="LIU Huanhua"]["bio_url"])