"""Validate saved dividend data before rendering or deploying."""
import argparse
import datetime
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

DATA = Path(__file__).resolve().parents[1] / 'data'
CURRENCIES = {'CAD', 'USD'}


def read(folder, name):
    return json.loads((folder / f'{name}.json').read_text())


def date(value):
    parsed = datetime.date.fromisoformat(value)
    if value != parsed.isoformat():
        raise ValueError(f'expected YYYY-MM-DD, got {value!r}')
    return parsed


def declaration(row, *, manual=False):
    amount = row['amount']
    if type(amount) not in (int, float) or not math.isfinite(amount) or not 0.0001 <= amount <= 25:
        raise ValueError(f'invalid amount {amount!r}')
    record, pay = date(row['record']), date(row['pay'])
    if not 0 < (pay - record).days <= 120:
        raise ValueError('payment must follow the record date by at most 120 days')
    source = urlsplit(row['source'])
    if source.scheme != 'https' or not source.hostname or source.username or source.password:
        raise ValueError('expected an HTTPS source')
    if manual:
        if row.get('announced') and date(row['announced']) > record:
            raise ValueError('announcement follows record date')
        if not row['quote'].strip():
            raise ValueError('missing investor-relations quote')
        return
    if source.netloc != 'www.sec.gov' or not source.path.startswith('/Archives/edgar/data/'):
        raise ValueError('expected an SEC EDGAR archive source')
    if row['currency'] is not None and row['currency'] not in CURRENCIES:
        raise ValueError(f'unsupported currency {row["currency"]!r}')
    if row['verified'] is not True or row['errors']:
        raise ValueError('unverified declaration')
    filed = date(row['file_date'])
    if row.get('first_filed') and date(row['first_filed']) > filed:
        raise ValueError('first filing follows source filing')


def validate_market(data, universe, baseline):
    latest = {}
    for ticker, company in data.items():
        if ticker not in universe or company['ticker'] != ticker or not company['name'].strip():
            raise ValueError(f'{ticker}: invalid company identity')
        for kind in ('regular', 'special'):
            previous = None
            for row in company[kind]:
                try:
                    declaration(row)
                    if row['ticker'] != ticker or row['special'] is not (kind == 'special'):
                        raise ValueError('ticker or payout type mismatch')
                    if kind == 'regular' and previous is not None and row['record'] >= previous:
                        raise ValueError('regular record dates must be unique and newest first')
                    previous = row['record']
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError(f'{ticker} {kind} {row.get("record")}: {error}') from error
        if company['regular']:
            latest[ticker] = company['regular'][0]['record']
    if not latest:
        raise ValueError('no verified regular dividends')
    lost = sorted(t for t, c in baseline.items()
                  if t in universe and c['regular'] and latest.get(t, '') < c['regular'][0]['record'])
    if lost:
        raise ValueError(f'latest regular declaration missing or older for {", ".join(lost)}')
    return len(latest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    try:
        for prefix in ('', 'us_'):
            universe = {row['ticker'] for row in read(DATA, prefix + 'universe')}
            name = prefix + 'parsed'
            baseline = read(args.baseline, name) if args.baseline else {}
            count = validate_market(read(DATA, name), universe, baseline)
            print(f'{name}: validated {count} companies with regular dividends')
        for ticker, rows in read(DATA, 'us_ir_manual').items():
            if not ticker.startswith('_'):
                if ticker not in universe:
                    raise ValueError(f'{ticker}: missing from US universe')
                for row in rows:
                    declaration(row, manual=True)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(1, f'Dividend validation failed: {error}\n')


if __name__ == '__main__':
    main()
