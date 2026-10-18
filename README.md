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

## Deploy (later)
Cloudflare Pages project "mapledividends"; output dir `dist`; custom domain mapledividends.com.
Option A (recommended): GitHub repo + `.github/workflows/build.yml`. It refreshes twice a day and deploys with wrangler. Needs secrets CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID, plus variable SEC_UA.
Option B (no GitHub): run `./build.sh` here, then `npx wrangler pages deploy dist --project-name=mapledividends` (needs a Cloudflare login/token). Data only refreshes when someone runs it.
