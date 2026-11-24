"""Render the dividend comparison calculator from the company-page datasets."""
import json
from pathlib import Path

PAYMENTS = {'Monthly': 12, 'Quarterly': 4, 'Semi-annual': 2, 'Annual': 1}
PATH = '/compare/'


def build(site, common):
    companies = []
    for market, prefix, rows in (('TSX', '/dividends/', site.CA_REGS),
                                 ('US', '/us/', site.US_REGS or [])):
        for row in sorted(rows, key=lambda item: item['ticker']):
            latest = row['regs'][0]
            payments = PAYMENTS.get(row['fq'])
            if not payments or latest['currency'] not in ('CAD', 'USD') or latest.get('currency_basis') == 'conflict':
                continue
            companies.append(dict(
                id=f"{market}:{row['ticker']}", name=row['name'], ticker=row['ticker'],
                market=market, path=f"{prefix}{row['slug']}/", amount=latest['amount'],
                currency=latest['currency'], payments=payments, frequency=row['fq'],
                amountLabel=site.money(latest['amount'], latest['currency']),
                record=site.dh(latest['record']), source=latest['source'],
            ))
    source = 'https://www.chemtradelogistics.com/news/chemtrade-logistics-income-fund-declares-november-2026-distribution/'
    if not any(c['id'] == 'TSX:CHE.UN' for c in companies):
        companies.append(dict(id='TSX:CHE.UN', ticker='CHE.UN', market='TSX',
                              name='Chemtrade Logistics Income Fund', amount=0.06,
                              currency='CAD', payments=12, frequency='Monthly',
                              close=15.56, closeDate='2026-11-23', closeCurrency='CAD',
                              amountLabel='C$0.06', record='Nov 30, 2026', source=source, path=source))
    movers = json.loads((Path(site.ROOT) / 'data/movers.json').read_text())
    for company in companies:
        saved = next((q for q in movers.get(company['market'], [])
                      if q['ticker'] == company['ticker']), None)
        if saved:
            company['close'] = saved['close']
            company['closeDate'] = saved['date']
            company['closeCurrency'] = saved['currency']
    (Path(site.DIST) / 'compare-symbols.json').write_text(json.dumps([c['id'] for c in companies]))
    site.write(PATH, site.env.get_template('compare.html').render(
        title='Compare Dividend Stocks and Project Growth | MapleDividends',
        description='Compare dividends and portfolio growth for two Canadian or U.S. stocks. Set your own assumptions and see the effect of reinvesting dividends.',
        path=PATH, crumb='Compare dividends', companies=companies, **common))
    return PATH
