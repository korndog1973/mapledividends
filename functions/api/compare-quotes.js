// Configure TWELVE_DATA_API_KEY with public-display rights for the covered markets.
export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const ids = [...new Set(['a', 'b'].map(key => url.searchParams.get(key)))];
  const values = {};
  if (!env.TWELVE_DATA_API_KEY) {
    try {
      const fx = await fetch('https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1', {cf: {cacheEverything:true, cacheTtl:3600}});
      const last = (await fx.json()).observations.at(-1);
      if (Number(last.FXUSDCAD.v) > 0) { values.fx = Number(last.FXUSDCAD.v); values.fxDate = last.d; }
    } catch { /* Manual exchange-rate input is still available. */ }
    return Response.json(values);
  }
  const symbols = await env.ASSETS.fetch(new URL('/compare-symbols.json', url));
  if (!symbols.ok) return Response.json({}, {status: 503});
  const allowed = new Set(await symbols.json());
  if (!ids.every(id => allowed.has(id))) return Response.json({}, {status: 400});
  async function read(endpoint, params) {
    const upstream = new URL('https://api.twelvedata.com/' + endpoint);
    upstream.search = new URLSearchParams({...params, apikey: env.TWELVE_DATA_API_KEY});
    const result = await fetch(upstream, {cf: {cacheEverything: true, cacheTtl: 900}});
    if (!result.ok) throw new Error('Quote unavailable');
    return result.json();
  }
  await Promise.allSettled(ids.map(async id => {
    const [market, ticker] = id.split(':');
    const params = {symbol: ticker, interval: '15min'};
    if (market === 'TSX') params.exchange = 'TSX';
    else params.country = 'United States';
    const q = await read('quote', params);
    if (q.symbol !== ticker || (market === 'TSX' && q.mic_code !== 'XTSE') ||
        (market === 'US' && !['XNAS','XNYS','XASE','ARCX','BATS'].includes(q.mic_code))) return;
    if (['CAD','USD'].includes(q.currency) && Number(q.close) > 0 && Number(q.timestamp) > 0) {
      values[id] = {price: Number(q.close), currency:q.currency, asOf:new Date(q.timestamp * 1000).toISOString()};
    }
  }).concat([ (async () => {
    const fx = await read('exchange_rate', {symbol:'USD/CAD'});
    if (fx.symbol === 'USD/CAD' && Number(fx.rate) > 0) values.fx = Number(Number(fx.rate).toFixed(4));
  })() ]));
  return Response.json(values);
}
