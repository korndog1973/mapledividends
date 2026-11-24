export function project({ investment, years, price, dividend, payments, dividendGrowth, priceGrowth, reinvest }) {
  let shares = investment / price;
  let cash = 0;
  let cumulative = 0;
  const history = [];
  for (let year = 1; year <= years; year++) {
    const payout = dividend * (1 + dividendGrowth) ** (year - 1);
    let income = 0;
    for (let payment = 1; payment <= payments; payment++) {
      const sharePrice = price * (1 + priceGrowth) ** (year - 1 + payment / payments);
      const received = shares * payout;
      income += received;
      if (reinvest) shares += received / sharePrice;
      else cash += received;
    }
    cumulative += income;
    const stockValue = shares * price * (1 + priceGrowth) ** year;
    history.push({ year, income, cumulative, stockValue, cash, total: stockValue + cash });
  }
  return history;
}

function setup(form) {
  const data = JSON.parse(document.getElementById('compare-companies').textContent);
  if (data.length < 2) return;
  const byId = new Map(data.map(company => [company.id, company]));
  const results = document.getElementById('compare-results');
  const heading = document.getElementById('compare-heading');
  const summary = document.getElementById('compare-summary');
  const table = document.getElementById('compare-years');
  const error = document.getElementById('compare-error');
  const fxLabel = document.getElementById('compare-fx');
  const control = name => form.elements.namedItem(name);
  const number = name => control(name).valueAsNumber;
  const company = side => byId.get(control(side).value);
  const money = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD', currencyDisplay: 'code' });
  const sides = ['a', 'b'];

  function element(tag, text) {
    const node = document.createElement(tag);
    node.textContent = text;
    return node;
  }

  function updateCompanies() {
    for (const side of sides) {
      const selected = company(side);
      const description = form.querySelector(`[data-dividend="${side}"]`);
      const source = element('a', 'Source');
      source.href = selected.source;
      description.replaceChildren(
        `Latest regular payout: ${selected.amountLabel} · ${selected.frequency} · Record date ${selected.record}. `, source,
      );
    }
    const usesUSD = sides.some(side => company(side).currency === 'USD');
    fxLabel.hidden = !usesUSD;
    control('fx').disabled = !usesUSD;
    control('fx').required = usesUSD;
  }

  const manual = new Set();
  let generation = 0;
  function fillPrice(side, price, currency, stamp) {
    if (manual.has(side + 'Price')) return;
    const converted = currency === 'USD' ? price * number('fx') : currency === 'CAD' ? price : NaN;
    if (!Number.isFinite(converted) || converted <= 0) return;
    const value = converted.toFixed(2);
    if (control(side + 'Price').value !== value) results.hidden = true;
    control(side + 'Price').value = value;
    form.querySelector('[data-price="' + side + '"]').textContent = 'Price as of ' + stamp;
  }
  async function refresh() {
    const version = ++generation;
    const params = new URLSearchParams(sides.map(side => [side, company(side).id]));
    const cached = side => {
      const c = company(side);
      if (c.close) fillPrice(side, c.close, c.closeCurrency, c.closeDate + ' (saved close)');
    };
    for (const side of sides) if (!control(side + 'Price').value) cached(side);
    autoCalculate();
    try {
      const response = await fetch('/api/compare-quotes?' + params);
      if (!response.ok) return;
      const quotes = await response.json();
      if (version !== generation) return;
      if (quotes.fx > 0 && !manual.has('fx')) {
        if (number('fx') !== quotes.fx) results.hidden = true;
        control('fx').value = quotes.fx;
        document.getElementById('fx-date').textContent = quotes.fxDate || '';
      }
      for (const side of sides) {
        if (!control(side + 'Price').value) cached(side);
        const quote = quotes[company(side).id];
        if (quote) fillPrice(side, quote.price, quote.currency, quote.asOf);
      }
      autoCalculate();
    } catch { /* Saved close and manual entry remain available. */ }
  }

  const query = new URLSearchParams(location.search);
  for (const side of sides) {
    if (byId.has(query.get(side))) control(side).value = query.get(side);
  }
  updateCompanies();
  form.hidden = false;
  window.setInterval(refresh, 15 * 60 * 1000);
  form.addEventListener('input', event => {
    let side = event.target.name;
    if (event.target.dataset.search) {
      side = event.target.dataset.search;
      const term = event.target.value.trim().toUpperCase();
      const matches = data.filter(c => c.ticker === term || c.id === term);
      const found = matches.length ? matches : data.filter(c => term && c.name.toUpperCase().includes(term));
      if (found.length !== 1) {
        event.target.setCustomValidity(term ? 'Enter a unique ticker, including TSX: or US: if needed, or clear the search.' : '');
        results.hidden = true;
        return;
      }
      event.target.setCustomValidity('');
      control(side).value = found[0].id;
    }
    if (side.endsWith('Price') || side === 'fx') manual.add(side);
    if (side === 'fx') refresh();
    if (sides.includes(side)) {
      const search = form.querySelector('[data-search="' + side + '"]');
      if (event.target === control(side)) search.value = '';
      search.setCustomValidity('');
      manual.delete(side + 'Price');
      control(side + 'Price').value = '';
      form.querySelector('[data-price="' + side + '"]').textContent = 'Enter a CAD price if a quote is unavailable.';
      updateCompanies();
      refresh();
    }
    results.hidden = true;
    error.hidden = true;
    autoCalculate();
  });

  function autoCalculate() {
    if (form.checkValidity() && company('a').id !== company('b').id) calculate(false);
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    calculate(true);
  });

  function calculate(focusResults) {
    if (company('a').id === company('b').id) {
      error.textContent = 'Choose two different companies.';
      error.hidden = false;
      return;
    }
    const years = Number(control('years').value);
    const runs = sides.map(side => {
      const selected = company(side);
      return project({
        investment: number('investment'), years, price: number(side + 'Price'),
        dividend: selected.amount * (selected.currency === 'USD' ? number('fx') : 1),
        payments: selected.payments, dividendGrowth: number(side + 'DividendGrowth') / 100,
        priceGrowth: number(side + 'PriceGrowth') / 100, reinvest: control('reinvest').checked,
      });
    });
    if (runs.some(run => run.some(point => !Number.isFinite(point.total) || !Number.isFinite(point.cumulative)))) {
      error.textContent = 'These assumptions produce values too large to calculate. Try a smaller growth rate or a shorter period.';
      error.hidden = false;
      return;
    }
    error.hidden = true;
    summary.replaceChildren();
    table.replaceChildren();
    sides.forEach((side, index) => {
      const selected = company(side);
      const end = runs[index].at(-1);
      const card = element('article', '');
      card.className = 'card';
      const link = element('a', `${selected.ticker} · ${selected.name}`);
      link.href = selected.path;
      const title = element('h3', '');
      title.append(link);
      const metrics = element('dl', '');
      for (const [label, value] of [
        ['Final-year dividend income', end.income],
        ['Cumulative dividends', end.cumulative],
        ['Ending value', end.total],
      ]) {
        metrics.append(element('dt', label), element('dd', money.format(value)));
      }
      card.append(title, metrics);
      summary.append(card);
    });
    for (let index = 0; index < years; index++) {
      for (const [slot, side] of sides.entries()) {
        const row = element('tr', '');
        const point = runs[slot][index];
        row.append(
          element('td', point.year), element('td', `${company(side).ticker} (${company(side).market})`),
          element('td', money.format(point.income)), element('td', money.format(point.total)),
        );
        table.append(row);
      }
    }
    heading.textContent = `${years}-year projection in Canadian dollars`;
    results.hidden = false;
    if (focusResults) heading.focus();
  }
  refresh();
}

if (typeof document !== 'undefined') {
  const form = document.getElementById('dividend-compare');
  if (form) setup(form);
}
