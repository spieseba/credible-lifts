"""Crawler for iwrp.net (run per page type; output is cached).

Run from the repo root: uv run python -m credible_lifts.ingest.crawl
"""

import json
import random
import time
from pathlib import Path

from credible_lifts.ingest.fetch import GaveUp, PermanentError, fetch_robust

IWRP = Path("data/raw/iwrp")
PAGE_TYPE = "athlete"       # "athlete" or "competition" - keep in sync with build_plan.py
PAGES = IWRP / "pages" / f"{PAGE_TYPE}s"
ID_KEY = f"{PAGE_TYPE}_id"
PLAN = IWRP / f"plan_{PAGE_TYPE}s.json"
JOURNAL = IWRP / f"journal_{PAGE_TYPE}s.jsonl"
PAUSE = 1.5
MAX_CONSECUTIVE_FAILURES = 3    # hard failures: 403s, timeouts, garbage 200s
MAX_CONSECUTIVE_REDIRECTS = 20  # dead-entry clusters are normal; 20 in a row means blocked
MAX_REQUESTS_PER_RUN = 1300     # nightly budget: stop below the per-IP cap, resume next night

class StopCrawl(Exception):
    """Something appears to be wrong. Quit and check."""


def save_atomic(path, text):
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)   # rename: atomic on the same filesystem

def read_journal(journal):
    if not journal.exists():
        return []
    with open(journal, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def log_attempt(journal, record):
    with open(journal, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def has_athlete_results(html):
    """A real, complete athlete page: right title template, body arrived whole."""
    return "wyniki, rekordy | IWRP" in html and html.rstrip().endswith("</html>")

def has_competition_results(html):
    """A real, complete competition page: right title template, body arrived whole."""
    return "competition results, records, statistics | IWRP" in html and html.rstrip().endswith("</html>")

has_results = {"athlete": has_athlete_results,
               "competition": has_competition_results}[PAGE_TYPE]

def crawl(plan, pages, journal, pause):
    """plan: list of {<PAGE_TYPE>_id, 'url'} rows."""
    pages.mkdir(parents=True, exist_ok=True)
    history = read_journal(journal)
    give_up_on = {r[ID_KEY] for r in history if r["outcome"] == "permanent"}
    seen_redirects = {r[ID_KEY] for r in history if r["outcome"] == "redirect"}
    seen_bad200 = {r[ID_KEY] for r in history if r["outcome"] == "bad200"}
    counts = {"cached": 0, "fetched": 0, "permanent": 0, "failed": 0}
    consecutive_failures = 0
    consecutive_redirects = 0
    to_fetch = sum(1 for e in plan if not (pages / f"{PAGE_TYPE}_{e[ID_KEY]}.html").exists())
    print(f"{len(plan)} planned, {to_fetch} to fetch, {len(plan) - to_fetch} already cached")
    started = time.monotonic()
    done = 0
    for item in plan:
        iid = item[ID_KEY]
        target = pages / f"{PAGE_TYPE}_{iid}.html"
        if target.exists():
            counts["cached"] += 1
            continue
        if iid in give_up_on:
            counts["permanent"] += 1
            continue
        record = {ID_KEY: iid}
        try:
            resp = fetch_robust(item["url"])
        except PermanentError as exc:
            record.update({"outcome": "permanent", "reason": str(exc)})
            counts["permanent"] += 1
            consecutive_failures += 1
        except GaveUp as exc:
            record.update({"outcome": "failed", "reason": str(exc)})
            counts["failed"] += 1
            consecutive_failures += 1
        else:
            if has_results(resp.text):
                save_atomic(target, resp.text)
                record.update({"outcome": "ok", "bytes": len(resp.text)})
                if resp.history:
                    record["redirected_to"] = resp.url
                counts["fetched"] += 1
                consecutive_failures = 0
                consecutive_redirects = 0
            elif resp.history and "429" in resp.url:
                # Redirected to 429.php: the site is throttling us. This is "slow
                # down", never "page gone" - so no verdict on this page, and we
                # stop rather than keep asking something already told us to wait.
                record.update({"outcome": "ratelimited", "reason": f"redirected to {resp.url}"})
                log_attempt(journal, record)
                raise StopCrawl(f"rate limited at {PAGE_TYPE} {iid} ({resp.url}) - "
                                "raise PAUSE and resume later")
            elif resp.history:
                # Redirected to the main page: deleted page OR a passing block
                # window - one sighting cannot tell. Two-strike rule: only a second
                # sighting on a later run is allowed to call it permanent.
                if iid in seen_redirects:
                    record.update({"outcome": "permanent",
                                   "reason": f"redirected again to {resp.url}"})
                    counts["permanent"] += 1
                else:
                    record.update({"outcome": "redirect",
                                   "reason": f"redirected to {resp.url}"})
                    counts["failed"] += 1
                    consecutive_redirects += 1
            else:
                # 200 but the body failed the results check: usually a truncated
                # body near the rate-limit window, not a dead page. Two-strike
                # rule: only a second sighting on a later run may call it
                # permanent (same logic as the redirect branch above).
                if iid in seen_bad200:
                    record.update({"outcome": "permanent",
                                   "reason": "200 without results again"})
                    counts["permanent"] += 1
                else:
                    record.update({"outcome": "bad200",
                                   "reason": "200 without results"})
                    counts["failed"] += 1
                consecutive_failures += 1
            time.sleep(pause) if pause is not None else time.sleep(random.uniform(0.7, 2.2))
        done += 1
        per = (time.monotonic() - started) / done
        eta = (to_fetch - done) * per / 60
        print(f"[{done:>4}/{to_fetch}] {record['outcome']:<9} {iid:<5} "
              f"~{eta:.0f} min left")
        log_attempt(journal, record)
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            raise StopCrawl(f"{consecutive_failures} failures in a row, last: {record}")
        if consecutive_redirects >= MAX_CONSECUTIVE_REDIRECTS:
            raise StopCrawl(f"{consecutive_redirects} redirects in a row, last: {record}")
        if done >= MAX_REQUESTS_PER_RUN:
            print(f"run budget reached ({done} requests) - stopping; resume after cool down")
            break
    return counts

if __name__ == "__main__":
    with open(PLAN, 'r', encoding="utf-8") as f:
        plan = json.load(f)
    counts = crawl(plan, PAGES, JOURNAL, PAUSE)
    print(counts)
