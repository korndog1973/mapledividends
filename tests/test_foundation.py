import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'site'), str(ROOT / 'pipeline')]
import build
import fetch_edgar
import validate


class DividendChangeTests(unittest.TestCase):
    def row(self, amount, currency, record):
        return dict(amount=amount, currency=currency, record=record,
                    file_date=record, snippet='')

    def test_equal_amount_cannot_hide_currency_switch(self):
        rows = [self.row(1, 'USD', '2026-10-01'),
                self.row(1, 'CAD', '2026-07-01'),
                self.row(0.9, 'CAD', '2026-04-01')]
        self.assertEqual(build.change(rows)['kind'], 'none')

    def test_missing_currency_cannot_produce_raise(self):
        rows = [self.row(1, 'USD', '2026-10-01'),
                self.row(0.9, None, '2026-07-01')]
        self.assertIsNone(build.change(rows)['pct'])

    def test_same_currency_raise_and_equal_amount(self):
        rows = [self.row(1.1, 'CAD', '2026-10-01'),
                self.row(1, 'CAD', '2026-07-01')]
        self.assertAlmostEqual(build.change(rows)['pct'], 10)
        rows[0]['amount'] = 1
        self.assertEqual(build.change(rows)['kind'], 'same')


class DataValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = validate.read(ROOT / 'data', 'parsed')
        self.baseline = copy.deepcopy(self.data)
        self.universe = {row['ticker'] for row in validate.read(ROOT / 'data', 'universe')}

    def test_committed_dataset(self):
        self.assertGreater(validate.validate_market(self.data, self.universe, self.baseline), 0)

    def test_lost_company_and_older_latest(self):
        ticker = next(t for t, c in self.data.items() if len(c['regular']) > 1)
        self.data[ticker]['regular'].pop(0)
        with self.assertRaisesRegex(ValueError, ticker):
            validate.validate_market(self.data, self.universe, self.baseline)
        self.data.pop(ticker)
        with self.assertRaisesRegex(ValueError, ticker):
            validate.validate_market(self.data, self.universe, self.baseline)

    def test_rejects_invalid_declarations(self):
        row = next(c['regular'][0] for c in self.data.values() if c['regular'])
        for fields in (dict(amount=float('nan')), dict(amount=True), dict(pay=row['record']),
                       dict(currency='XYZ'), dict(source='https://example.com/'), dict(verified=False)):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                validate.declaration(dict(row, **fields))


class EdgarTests(unittest.TestCase):
    def test_rejects_partial_search(self):
        with patch.object(fetch_edgar, 'get', return_value=b'{"timed_out": true, "hits": {"hits": []}}'):
            with self.assertRaisesRegex(ValueError, 'partial'):
                fetch_edgar.search(1, 'dividend')

    def test_rejects_missing_search_results(self):
        with patch.object(fetch_edgar, 'get', return_value=b'{}'):
            with self.assertRaises(KeyError):
                fetch_edgar.search(1, 'dividend')
