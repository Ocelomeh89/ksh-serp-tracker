# KSH SERP Tracker

Weekly SerpAPI tracker + Streamlit dashboard for Kauai Shores Hotel SERP environment.

Tracks **AI Overview presence**, **OTA paid share**, **Google Hotel Pack** appearances, and **KSH organic/citation status** across 50 queries × 2 devices (desktop + mobile), US-wide.

Design: [`docs/superpowers/plans/2026-05-20-ksh-serp-tracker.md`](docs/superpowers/plans/2026-05-20-ksh-serp-tracker.md)

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env and set SERPAPI_API_KEY

pytest                              # run test suite
python -m ksh_serp.scraper          # full weekly scrape
streamlit run dashboard/app.py      # open dashboard
```

## What's tracked

Per `(run_date, query, device)`:

- AI Overview presence + cited sources (and whether KSH is one of them)
- Paid ads on the SERP, filtered to known OTA domains
- Hotel Pack appearances and whether KSH is in the pack
- KSH organic position (or null if not in top 100)
- Top 3 organic domains
- Screenshot URL from SerpAPI

## Repo layout

```
src/ksh_serp/
  config.py         # paths, env, enums, KSH/OTA domain registries
  classifier.py     # is_ksh, is_ota, extract_domain
  parser.py         # SerpAPI response → flat row
  db.py             # SQLite schema + insert/fetch
  serpapi_client.py # thin SDK wrapper + raw-response archive
  scraper.py        # orchestrate full keyword × device pass
dashboard/app.py    # Streamlit, 4 tabs
data/
  keywords.csv      # 25 brand + 25 nonbrand seed
  ota_domains.txt   # OTA domain registry
  serp.db           # SQLite history (committed)
tests/              # pytest, ~38 tests
.github/workflows/scrape.yml  # weekly cron
```

## Cadence

Weekly via GitHub Actions, Mondays 14:00 UTC (~04:00 HST). Manual run from terminal: `python -m ksh_serp.scraper`. Manual workflow trigger from GitHub Actions tab.

## Editing what's tracked

Edit `data/keywords.csv`. Columns: `query,type,page`. `type` is `brand` or `nonbrand`. `page` is the KSH URL the keyword belongs to (`/`, `/dining`, `/specials`, `/rooms`) — used for the Non-Brand Page Tracker tab.

Edit `data/ota_domains.txt` (one domain per line, `#` for comments) to expand the OTA registry.

## Volume + cost

- 50 queries × 2 devices × 4 runs/mo = ~400 SerpAPI searches/month
- SerpAPI Hobby plan ($75/mo, 5,000 searches): >10× headroom

## Tests

```bash
pytest -v
```

Parser tests run against hand-crafted fixtures in `tests/fixtures/`. To re-capture against real SerpAPI responses:

```bash
python scripts/capture_fixture.py "kauai shores hotel" desktop brand_aio_desktop
```

## License

See `LICENSE`.
