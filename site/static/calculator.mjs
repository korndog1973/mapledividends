export function project({ investment, years, yieldPct, growthPct, reinvest }) {
  const y = yieldPct / 100;
  const g = growthPct / 100;
  let shares = investment; // flat $1 share price: no share-price growth assumed
  let cash = 0;
  let cumulative = 0;
  const history = [];
  for (let year = 1; year <= years; year++) {
    const payout = y * (1 + g) ** (year - 1); // dividend per $1 share
    const income = shares * payout;
    if (reinvest) shares += income; // buy more shares at $1
    else cash += income;
    cumulative += income;
    history.push({ year, income, cumulative, total: shares + cash });
  }
  return history;
}

function setup(form) {
  const results = document.getElementById('calc-results');
  const heading = document.getElementById('calc-heading');
  const summary = document.getElementById('calc-summary');
  const table = document.getElementById('calc-years');
  const error = document.getElementById('calc-error');
  const reverse = document.getElementById('calc-reverse');
  const target = document.getElementById('calc-target');
  const required = document.getElementById('calc-required');
  const control = name => form.elements.namedItem(name);
  const number = name => control(name).valueAsNumber;
  const money = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD', currencyDisplay: 'code' });

  function element(tag, text) {
    const node = document.createElement(tag);
    node.textContent = text;
    return node;
  }

  function updateReverse() {
    const y = number('yield');
    const t = target.valueAsNumber;
    if (!(t > 0)) {
      required.textContent = '';
      return;
    }
    if (!(y > 0)) {
      required.textContent = 'Enter a yield above 0% to work out the investment needed.';
      return;
    }
    required.textContent = `You'd need ${money.format((t * 12) / (y / 100))} invested at a ${y}% yield.`;
  }

  function card(title, rows) {
    const node = element('article', '');
    node.className = 'card';
    const h = element('h3', title);
    const metrics = element('dl', '');
    for (const [label, value] of rows) {
      metrics.append(element('dt', label), element('dd', value));
    }
    node.append(h, metrics);
    return node;
  }

  form.hidden = false;
  reverse.hidden = false;
  updateReverse();
  target.addEventListener('input', updateReverse);

  form.addEventListener('input', () => {
    results.hidden = true;
    error.hidden = true;
    updateReverse();
  });

  form.addEventListener('submit', event => {
    event.preventDefault();
    const years = Number(control('years').value);
    const investment = number('investment');
    const run = project({
      investment, years,
      yieldPct: number('yield'),
      growthPct: number('growth'),
      reinvest: control('reinvest').checked,
    });
    if (run.some(point => !Number.isFinite(point.income) || !Number.isFinite(point.total) || !Number.isFinite(point.cumulative))) {
      error.textContent = 'These assumptions produce values too large to calculate. Try a smaller growth rate or a shorter period.';
      error.hidden = false;
      return;
    }
    error.hidden = true;
    summary.replaceChildren();
    table.replaceChildren();
    const first = run[0];
    const end = run.at(-1);
    const gain = end.total - investment;
    const gainPct = investment > 0 ? (gain / investment) * 100 : 0;
    summary.append(
      card('Dividend income', [
        ['Annual income now', money.format(first.income)],
        ['Monthly income now', money.format(first.income / 12)],
        [`Annual income in year ${years}`, money.format(end.income)],
        [`Monthly income in year ${years}`, money.format(end.income / 12)],
      ]),
      card('Ending value', [
        ['Cumulative dividends', money.format(end.cumulative)],
        ['Ending value', money.format(end.total)],
        ['Growth vs starting investment', `${gain >= 0 ? '+' : ''}${money.format(gain)} (${gainPct.toFixed(1)}%)`],
      ]),
    );
    for (const point of run) {
      const row = element('tr', '');
      row.append(
        element('td', point.year),
        element('td', money.format(point.income)),
        element('td', money.format(point.cumulative)),
        element('td', money.format(point.total)),
      );
      table.append(row);
    }
    heading.textContent = `${years}-year projection in Canadian dollars`;
    results.hidden = false;
    heading.focus();
  });
}

if (typeof document !== 'undefined') {
  const form = document.getElementById('dividend-calculator');
  if (form) setup(form);
}
