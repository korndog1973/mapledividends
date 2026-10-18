#!/usr/bin/env bash
# MapleDividends build: refresh data from SEC EDGAR, parse, generate static site into dist/
# Usage: ./build.sh            (full: fetch + parse + build)
#        SKIP_FETCH=1 ./build.sh  (rebuild site from cached data)
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q -r requirements.txt 2>/dev/null || python3 -m pip install -q --break-system-packages -r requirements.txt
if [ -z "${SKIP_FETCH:-}" ]; then
  if ls pipeline/issuers_*.xlsx >/dev/null 2>&1; then python3 pipeline/universe.py; else echo "No TSX issuer list (internal file); using committed data/universe.json"; fi
  python3 pipeline/fetch_edgar.py
  DATASET=us MAXDOCS=24 python3 pipeline/fetch_edgar.py   # Stars & Syrup (U.S. section)
fi
python3 pipeline/parse.py
DATASET=us python3 pipeline/parse.py
python3 site/build.py
