# credible-lifts
![CI](https://github.com/spieseba/credible-lifts/actions/workflows/ci.yml/badge.svg)

The goal of this project is to quantitatively model real Olympic weightlifting performances from messy longitudinal data. 

Can past competition results predict an athlete's next total (Snatch + Clean & Jerk) and how well? 

**Status:** initial dataset built; SQL/pandas data quality/cleaning investigation is in progress, with event and athlete entity resolution next. 


## Data

The dataset is built from [IWRP](https://iwrp.net) (an extensive weightlifting results database) and comprises per-competition and per-athlete pages.
The per-athlete pages carry full career results including individual attempts. The parsed data contains 207,880 results from 3,598 competitions (1928–2026) and bios for the 19,302 athletes with at least three valid results. The scrape stayed polite: rate-limited with backoff, honoring the site's request limits by crawling in small batches, every page fetched exactly once into a local cache. All parsing and re-parsing run offline against that cache.

Along with the usual messiness (e.g. missing, invalid, implausible values), the cached data has some quirks that need to be addressed before continuing to the modeling phase:
- **Three-lift era.** Until 1972 an Olympic weightlifting total included the clean & press. Pre-1973 totals are therefore not comparable to modern two-lift totals.
- **Duplicated competitions and athlete identities.** One physical performance may appear under several competitions due to combined events (e.g. the Olympics doubled as World Championships before 1984). Due to different transliterations ("Pisarenko Anatoliy = Pisarenko Anatoli") lifts of the same athlete may be listed under different ids. 
- **Birthdate precision.** For a lot of athletes only the birth year is known.

This is a personal project which is not affiliated with or endorsed by IWRP or the International Weightlifting Federation (IWF). No ownership of the results data is claimed: all rights in the underlying competition data remain with their respective owners. This repository redistributes no scraped content. Neither the raw page cache nor the derived dataset is part of the repo. The data is used for non-commercial analysis only. 

## Modeling

Forecast models and calibrated prediction intervals are not yet established.


## API

A dummy is already deployed on Cloud Run: the endpoint is reachable, the prediction is a placeholder (mean of recent totals ± fixed margin):

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
