# credible-lifts
![CI](https://github.com/spieseba/credible-lifts/actions/workflows/ci.yml/badge.svg)

Forecasting Olympic weightlifting totals with *credible* intervals.

Competition results can be seen as noisy measurements of a latent quantity: an 
athlete's true strength on that day. This project builds its own dataset by 
scraping the [IWF results archive](https://iwf.sport/results/results-by-events/), 
then models athlete development to predict the total (Snatch + Clean & Jerk) at an 
athlete's **next** competition as a calibrated uncertainty interval.

**Status: early exploration.** Site recon and a first event-page parser are done;
the scraper for the full archive is in progress. Model, data layer, and serving
come after.

## Data

Self-scraped from the public IWF results archive, politely: rate-limited,
every page fetched once and cached locally. Parsing runs offline against
the cache. The raw HTML cache is not part of this repo.

This project is not affiliated with or endorsed by the International
Weightlifting Federation (IWF). No ownership of the results data is claimed:
all rights in the underlying competition data remain with the IWF and/or
their respective owners. This repository redistributes no scraped content;
the data is used for non-commercial analysis only.

## License

Code is released under the [MIT License](LICENSE).
