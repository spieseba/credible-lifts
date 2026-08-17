# credible-lifts
![CI](https://github.com/spieseba/credible-lifts/actions/workflows/ci.yml/badge.svg)

Forecasting Olympic weightlifting totals with *credible* intervals.

Competition results can be seen as noisy measurements of a latent quantity: an athlete's true strength on that day. This project builds its own dataset from public competition results, then models athlete development to predict the total (Snatch + Clean & Jerk) at an athlete's **next** competition as a calibrated uncertainty interval.

**Status:** dataset built with 143,157 competition results from 18,576 athletes (1928–2026), scraped and processed locally.
A dummy API is live on Cloud Run, where the prediction is a placeholder at the moment. Next: SQL data layer, then baseline models.

## Data

The dataset is built from [IWRP](https://iwrp.net) (a weightlifting results database), whose per-athlete pages carry full career results including individual attempts. It includes only athletes with at least three valid results (positive totals, i.e. bomb-outs don't count), a bar (pun intended) re-applied after all cleaning steps. The scrape stayed polite: rate-limited with backoff, honoring the site's request limits by crawling in small batches, every page fetched exactly once into a local cache. All parsing and re-parsing run offline against that cache.

This is a personal project which is not affiliated with or endorsed by IWRP or the International Weightlifting Federation (IWF). No ownership of the results data is claimed: all rights in the underlying competition data remain with their respective owners. This repository redistributes no scraped content. Neither the raw page cache nor the derived dataset is part of the repo. The data is used for non-commercial analysis only.

### Data notes

Some quirks of the data:

- **Three-lift era.** Until 1972 the Olympic total included the clean & press. Pre-1973 totals are therefore not comparable to modern two-lift totals; ~3,300 rows in the dataset have snatch + clean & jerk ≠ total, almost all pre-1973.
- **Cross-listed championships.** One physical performance can appear under several championships: Junior and Senior editions of the same meet, combined events, and the Olympics doubling as World Championships before 1984. The dataset deduplicates on (athlete, date, total). Thus, there is one row per physical performance.
- **Birthdate precision.** For ~45% of athletes only the birth year is known. Year-only birthdates are imputed to July 1 (≤ 6 months error) and flagged in a `birthdate_precision` column; January 1 birthdates are treated as year-only placeholders (they occur ~30× more often than chance would allow).

## API

A dummy is deployed on Cloud Run: the endpoint is reachable, the prediction is a placeholder (mean of recent totals ± fixed margin) until a model lands.

```bash
curl -X POST https://credible-lifts-uqy2r54oza-ew.a.run.app/predict \
  -H "Content-Type: application/json" \
  -d '{"athlete": "Naim Suleymanoglu", "bodyweight_kg": 64.0, "recent_totals_kg": [320, 325, 330]}'
```

```json
{"predicted_total_kg": 325.0, "p10_kg": 313.0, "p90_kg": 337.0}
```

## License

Code is released under the [MIT License](LICENSE). The dataset is not distributed with this repository.
