#!/usr/bin/env bash
# Full refresh by default. SKIP_FETCH=1 builds from the saved parsed datasets.
set -euo pipefail
cd "$(dirname "$0")"

if [[ -z "${SKIP_FETCH:-}" ]]; then
  backup=$(mktemp -d)
  files=(universe manifest us_manifest parsed us_parsed build_stats movers power_prices)
  for name in "${files[@]}"; do
    if [[ -f "data/$name.json" ]]; then cp "data/$name.json" "$backup/"; fi
  done
  cleanup() {
    local status=$?
    if (( status != 0 )); then
      for name in "${files[@]}"; do
        if [[ -f "$backup/$name.json" ]]; then
          cp "$backup/$name.json" data/
        else
          rm -f "data/$name.json"
        fi
      done
    fi
    rm -rf "$backup"
  }
  trap cleanup EXIT
  if compgen -G 'pipeline/issuers_*.xlsx' > /dev/null; then python3 pipeline/universe.py; fi
  python3 pipeline/fetch_edgar.py
  DATASET=us MAXDOCS=24 python3 pipeline/fetch_edgar.py
  python3 pipeline/parse.py
  python3 pipeline/bigpayers.py
  DATASET=us python3 pipeline/parse.py
  python3 pipeline/validate.py --baseline "$backup"
else
  export MOVERS_OFFLINE=1
  python3 pipeline/validate.py
fi
python3 site/build.py
