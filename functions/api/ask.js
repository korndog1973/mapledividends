// Ask MapleDividends: POST /api/ask {q} -> {answer, as_of, links, left} . Cloudflare Pages Function, Workers AI FREE plan only.
// Answers ONLY from /ask-data.json (built by site/ask.py). Safeguards: 300-char question, 300-token answer,
// 400 questions/day site-wide, 10/day per visitor, identical questions cached for the UTC day (cost 0 neurons).
// Counters use KV (binding ASK_KV) when bound; otherwise a best-effort per-data-centre counter in the Cache API.
// Either way the Workers AI Free plan hard-stops at 10,000 neurons/day, so this can never bill.
const MODEL = '@cf/meta/llama-3.1-8b-instruct-fp8-fast';
const GLOBAL_CAP = 400, VISITOR_CAP = 10, MAX_Q = 300, MAX_TOKENS = 300, MAX_ROWS = 20;
const SYSTEM = 'You are the MapleDividends data helper. Answer ONLY from the DATA rows below. If the answer is not in the DATA, reply exactly: "I don\'t know. That isn\'t in our data yet." Never recommend buying, selling or holding anything, and never give personal financial advice; if asked, say you can only share the data. Do not guess or use outside knowledge. Give amounts, dates and currencies exactly as written. Plain text, max 120 words.';
const STOP = new Set('the and for with what when whats next does did is are was its it of on in to a an me my i you how much many which who will any about tell show from that this there their has have do be or at by per share shares stock stocks dividend dividends pay paid payout date dates ex canada canadian inc corp'.split(' '));
const CAPPED_MSG = "We've hit today's free question limit. Try again tomorrow, or get our free weekly newsletter for dividend raises, cuts and ex-dates.";
const VISITOR_MSG = "That's your 10 free questions for today. Come back tomorrow, or get our free weekly newsletter for dividend raises, cuts and ex-dates.";

let DATA = null, DATA_DAY = null;
const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
const day = () => new Date().toISOString().slice(0, 10); // UTC day = Workers AI neuron reset
async function sha(s) { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('').slice(0, 32); }

async function loadData(env, request) {
  if (DATA && DATA_DAY === day()) return DATA;
  const r = await env.ASSETS.fetch(new Request(new URL('/ask-data.json', request.url)));
  if (!r.ok) throw new Error('no data');
  DATA = await r.json(); DATA_DAY = day(); return DATA;
}

export function retrieve(data, q) {
  const raw = q.replace(/[^A-Za-z0-9.\- ]/g, ' ');
  const words = raw.toLowerCase().split(/\s+/).filter(Boolean);
  const upper = new Set(raw.split(/\s+/).filter(w => /^[A-Z][A-Z.\-]{0,5}$/.test(w)).map(w => w.replace(/\.$/, '')));
  const lw = new Set(words.map(w => w.replace(/\.$/, '')));
  const content = [...lw].filter(w => w.length >= 3 && !STOP.has(w));
  const scored = [];
  for (const r of data.rows) {
    let s = 0;
    const tks = r.t ? [r.t] : (r.tk || []);
    for (const t of tks) {
      // short/ambiguous tickers (T, BCE in lowercase prose) only count when typed in capitals or 3+ letters
      if (upper.has(t)) s += 10; else if (t.length >= 3 && lw.has(t.toLowerCase())) s += 6;
    }
    for (const w of content) if (r.k.includes(w)) s += 4;
    if (s) scored.push([s, r]);
  }
  const ql = q.toLowerCase();
  const topic = (g, w) => data.rows.filter(r => r.g.includes(g)).map(r => [w, r]);
  if (/power|data ?cent(re|er)|\bai\b|megawatt|\bmw\b|grid|electric/.test(ql)) scored.push(...topic('power', 2));
  if (/rais|hike|increas|deadly|grow/.test(ql)) scored.push(...topic('raise', 2));
  if (/\bcut|decreas|lower|slash|not deadly/.test(ql)) scored.push(...topic('cut', 2));
  if (/upcoming|next|this week|soon|coming|calendar/.test(ql) && !scored.length) scored.push(...data.rows.filter(r => r.ex).sort((a, b) => a.ex < b.ex ? -1 : 1).slice(0, 15).map(r => [1, r]));
  if (/mover|biggest|drop|fell|fall|gain|jump|up today|down today|price/.test(ql)) {
    const mv = data.rows.filter(r => r.g.includes('mover')).sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct));
    scored.push(...mv.slice(0, 10).map(r => [1.5, r]));
  }
  const seen = new Set(), out = [];
  for (const [, r] of scored.sort((a, b) => b[0] - a[0])) { if (seen.has(r.x)) continue; seen.add(r.x); out.push(r); if (out.length >= MAX_ROWS) break; }
  return out;
}

// --- counters (KV if bound, else Cache API best effort) ---
async function getCount(env, key) {
  if (env.ASK_KV) return parseInt(await env.ASK_KV.get(key) || '0', 10);
  const r = await caches.default.match(`https://ask-counter.internal/${key}`); return r ? parseInt(await r.text(), 10) || 0 : 0;
}
async function setCount(env, key, n) {
  if (env.ASK_KV) return env.ASK_KV.put(key, String(n), { expirationTtl: 172800 });
  return caches.default.put(`https://ask-counter.internal/${key}`, new Response(String(n), { headers: { 'cache-control': 'max-age=90000' } }));
}

export async function onRequestPost({ request, env, waitUntil }) {
  let body; try { body = await request.json(); } catch { return json({ error: 'Send JSON: {"q": "your question"}' }, 400); }
  const q = String(body && body.q || '').replace(/\s+/g, ' ').trim();
  if (!q) return json({ error: 'Type a question first.' }, 400);
  if (q.length > MAX_Q) return json({ error: `Keep it under ${MAX_Q} characters, please.` }, 400);
  if (!env.AI) return json({ error: 'The Q&A box is switched off right now.', capped: true }, 503);
  const d = day();
  const data = await loadData(env, request);
  const norm = q.toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ');
  const cacheKey = new Request(`https://ask-cache.internal/${d}/${data.as_of}/${await sha(norm)}`);
  const ip = request.headers.get('cf-connecting-ip') || 'anon';
  const vKey = `ask:v:${d}:${await sha(ip + '|' + d)}`, gKey = `ask:g:${d}`;
  const [vN, gN] = await Promise.all([getCount(env, vKey), getCount(env, gKey)]);
  if (vN >= VISITOR_CAP) return json({ capped: 'visitor', answer: VISITOR_MSG, left: 0 });
  const hit = await caches.default.match(cacheKey);
  if (hit) { const o = await hit.json(); return json({ ...o, cached: true, left: VISITOR_CAP - vN }); } // repeats are free and don't count
  if (gN >= GLOBAL_CAP) return json({ capped: 'global', answer: CAPPED_MSG, left: VISITOR_CAP - vN });

  const rows = retrieve(data, q);
  const links = [...new Set(rows.map(r => r.u))].slice(0, 3);
  let answer;
  if (!rows.length) {
    answer = "I don't know. That isn't in our data yet. Try a TSX ticker or company name (like BCE or Bank of Montreal), or check the ex-dividend calendar.";
  } else {
    // count before calling the model so parallel bursts can't blow past the cap
    await Promise.all([setCount(env, vKey, vN + 1), setCount(env, gKey, gN + 1)]);
    const ctx = rows.map((r, i) => `${i + 1}. ${r.x}`).join('\n');
    try {
      const res = await env.AI.run(MODEL, { max_tokens: MAX_TOKENS, temperature: 0.1, messages: [
        { role: 'system', content: `${SYSTEM}\n\nDATA (MapleDividends, as of ${data.as_of_h}):\n${ctx}` },
        { role: 'user', content: q }] });
      answer = String(res && res.response || '').trim() || "I don't know. That isn't in our data yet.";
    } catch (e) {
      return json({ capped: 'global', answer: "The Q&A box is resting for today. Try again tomorrow, or get our free weekly newsletter.", left: VISITOR_CAP - vN - 1 });
    }
  }
  const out = { answer, as_of: data.as_of_h, links };
  waitUntil(caches.default.put(cacheKey, new Response(JSON.stringify(out), { headers: { 'content-type': 'application/json', 'cache-control': 'max-age=86400' } })));
  return json({ ...out, left: VISITOR_CAP - vN - (rows.length ? 1 : 0) });
}
export const onRequestGet = () => json({ error: 'POST a JSON body: {"q": "When is BMO\'s next ex-date?"}' }, 405);
