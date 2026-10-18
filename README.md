# MapleDividends: static site + data pipeline

Free stack: Python, Jinja2, SEC EDGAR (public domain), Cloudflare Pages (static).

## Commands
- Full build (fetch EDGAR, parse, generate dist/): `./build.sh`
- Rebuild from cached data: `SKIP_FETCH=1 ./build.sh`
- Pin the "today" date: `BUILD_DATE=2026-10-16 SKIP_FETCH=1 ./build.sh`
- Local preview: `cd dist && python3 -m http.server 8787` then open http://127.0.0.1:8787

## Data rules
- Sources: SEC EDGAR 6-K/8-K exhibits only. No CNW, GlobeNewswire, TMX, RBC or TSX Trust scraping.
- Publishing: a declaration is published only if it has an amount, a record date and a pay date, and passes these checks: amount 0–25; record date within -10/+150 days of filing; pay date after record date and within 120 days; not preferred shares or debentures; not a comparison amount.
- Conflicts: where one record date has conflicting amounts, the majority wins only if it has at least 2x the support. Otherwise it's dropped.
- Manual exclusions: `pipeline/exclusions.json`.
- Ex-date = record date (Canada T+1). Currency is shown only if the filing states it.
- `pipeline/issuers_*.xlsx` (TSX issuer list) is copyrighted. It's for internal use only and is gitignored. `data/universe.json` (ticker, name, CIK) is what gets committed.
- Set `SEC_UA` to a real, monitored contact email. SEC fair-access policy requires it.

## Stars & Syrup (U.S. section)
- Universe: `data/us_universe.json` (ticker, name, CIK list, exchange). Pages: `/stars-and-syrup/` and `/us/<ticker>/` (`site/syrup.py`, `site/templates/syrup.html`).
- Data: same pipeline with `DATASET=us` (`data/us_manifest.json` -> `data/us_parsed.json`). Reads 8-K, 10-Q and 10-K, because many U.S. issuers only state record and pay dates in quarterly reports. U.S.-only parser rules are gated on `DATASET=us`, so the TSX output is unchanged.
- Amounts are shown in US$ (U.S. issuers write a plain "$"). Ex-date = record date (U.S. T+1 since May 28, 2024).
- `data/us_ir_manual.json`: declarations a person copied from a company's own IR announcement because EDGAR doesn't have them yet. Each needs its IR URL. Remove once EDGAR has it. `IR_MANUAL_NOTES.md` lists every entry and the filing that should replace it.
- Companies with no verified declaration are listed as "not covered yet" on the index instead of guessed.

## Leaky Maple vs Golden Pour (/leaky-maple/)
- `site/leaky.py`, `site/templates/leaky.html`, `site/templates/_leaky.html` (SVG art macros), styles at the end of `site/static/style.css`.
- **Leaky Maple** 🍁: the worst dividend cut ("Not Deadly") first filed in the last 12 weeks goes on the sap bucket. **Golden Pour** 🥞: the biggest raise ("Deadly") goes on the pancake flag. If the window has none, the most recent one is shown with its filing date. Same rules as `/raises-and-cuts/` (changes we can't date are left out). The 🇺🇸 tab does the same with Stars & Syrup data.
- **Data source:** our own EDGAR-verified dividend data only. No price data is fetched or stored, so there's no API key, licence or extra cron; the existing twice-daily build refreshes it. We looked for a free TSX daily-close feed for a "worst stock of the day" version and found none whose free terms allow showing prices on a public site (Stooq is behind a bot wall; Alpha Vantage, Marketstack, EODHD, FMP free tiers are personal/non-commercial; Twelve Data and Finnhub TSX are paid).
- **Live movers:** TradingView's free embeddable "Stock Market" (hotlists) widget, exchange `TSX` (and `US` on the U.S. tab), injected by a small script only when its reserved-height slot scrolls into view. It runs in the visitor's browser from TradingView under TradingView's widget terms; prices are delayed and are price moves, not dividends. The widget has no setting to open on Losers/Gainers, so the captions tell people which tab to tap. Covered on the privacy page.
- **Share image:** `dist/leaky-maple/og.png` (1200x630, both tickers) is drawn at build time with Pillow (`requirements.txt`). If Pillow is missing the page just has no og:image.
- Animations are CSS and stop under `prefers-reduced-motion`.

## Deploy (later)
Cloudflare Pages project "mapledividends"; output dir `dist`; custom domain mapledividends.com.
Option A (recommended): GitHub repo + `.github/workflows/build.yml`. It refreshes twice a day and deploys with wrangler. Needs secrets CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID, plus variable SEC_UA.
Option B (no GitHub): run `./build.sh` here, then `npx wrangler pages deploy dist --project-name=mapledividends` (needs a Cloudflare login/token). Data only refreshes when someone runs it.
