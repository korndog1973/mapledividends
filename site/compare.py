"""Render the dividend comparison calculator from the company-page datasets."""
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
    site.write(PATH, site.env.get_template('compare.html').render(
        title='Compare Dividend Stocks and Project Growth | MapleDividends',
        description='Compare dividends and portfolio growth for two Canadian or U.S. stocks. Set your own assumptions and see the effect of reinvesting dividends.',
        path=PATH, crumb='Compare dividends', companies=companies, **common))
    return PATH
