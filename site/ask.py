"""Ask MapleDividends: writes dist/ask-data.json, the only data the /api/ask chat function may answer from.
One compact text row per fact (TSX payers, U.S. payers, last-close movers, power projects), each with match keys
(ticker + significant name words). The Pages Function retrieves up to ~20 rows per question and sends them to Workers AI."""
import json, os, re
STOP={'inc','corp','corporation','limited','ltd','company','co','the','group','trust','fund','holdings','plc','sa','and','of','international','incorporated','canada','canadian','partners','lp','reit'}
def words(name): return sorted({w for w in re.findall(r'[a-z0-9]+',name.lower()) if len(w)>=3 and w not in STOP})
def _payers(B,data,market):
    out=[]
    for t,c in data.items():
        regs=c.get('regular') or []
        if not regs: continue
        L=regs[0]; fq=B.freq(c); ch=B.change(regs,fq)
        up=sorted([r for r in regs+c.get('special',[]) if r.get('record') and B.D(r['record'])>=B.TODAY],key=lambda r:r['record'])
        s=B.slug(t); url=(f"/dividends/{s}/" if market=='TSX' else f"/us/{s}/")
        txt=(f"{c['name']} ({market}: {t}). Latest regular dividend {B.money(L['amount'],L['currency'] or ('USD' if market=='US' else None))} per share, "
             f"record/ex-date {B.dh(L['record'])}, paid {B.dh(L['pay'])}, frequency {fq}. Source filing dated {B.dh(L['file_date'])}.")
        if up: txt+=f" Next ex-date on file: {B.dh(up[0]['record'])} ({B.money(up[0]['amount'],up[0]['currency'] or ('USD' if market=='US' else None))}, paid {B.dh(up[0]['pay'])})."
        if ch.get('kind') in ('raise','cut') and ch.get('pct') is not None: txt+=f" Latest change: {'raise' if ch['kind']=='raise' else 'cut'} of {ch['pct']:+.1f}% (first filed {B.dh(ch['first_filed'])})."
        elif ch.get('kind')=='same': txt+=" Latest dividend unchanged from the previous one."
        tags=['dividend',market.lower()]+(['upcoming'] if up else [])+([ch['kind']] if ch.get('kind') in ('raise','cut') else [])
        out.append(dict(t=t,k=words(c['name']),g=tags,u=url,x=txt,ex=up[0]['record'] if up else None))
    return out
def build(B):
    rows=[]
    rows+=_payers(B,{t:dict(c,name=B.display_name(c['name'])) for t,c in json.load(open(os.path.join(B.ROOT,'data','parsed.json'))).items()},'TSX')
    try: rows+=_payers(B,json.load(open(os.path.join(B.ROOT,'data','us_parsed.json'))),'US')
    except (OSError,ValueError): pass
    try: mv=json.load(open(os.path.join(B.ROOT,'data','movers.json')))
    except (OSError,ValueError): mv={}
    for mkt,lst in mv.items():
        if not isinstance(lst,list): continue
        for m in lst:
            cur='C$' if m.get('currency')=='CAD' else 'US$'
            m=dict(m,name=B.display_name(m['name']))
            rows.append(dict(t=m['ticker'],k=words(m['name']),g=['mover',mkt.lower()],u=('/dividends/' if mkt=='TSX' else '/us/')+m['slug']+'/',
                x=f"Price move: {m['name']} ({m['ticker']}) closed at {cur}{m['close']:.2f} on {B.dh(m['date'])}, {m['pct']:+.2f}% vs the previous close ({cur}{m['prev']:.2f}).",pct=m['pct']))
    p=os.path.join(B.ROOT,'data','power_projects.json')
    if os.path.exists(p):
        import power
        for r in json.load(open(p))['rows']:
            tks=[t for t,_ in r['tickers']]
            rows.append(dict(t=None,tk=tks,k=words(r['project']+' '+r['location']+' '+' '.join(power.NAMES.get(t,'') for t in tks)),g=['power','datacentre',r['province'].lower()],u='/power-grid/',
                x=f"Power/data centre project: {r['project']} in {r['location']}, {r['province']}. size {(r['mw']+' MW') if (r.get('mw') or '').replace(',','').isdigit() else (r.get('mw') or 'not stated')}, status: {r['status']}, announced {r.get('announced') or 'n/a'}. Tickers: {', '.join(tks)}. {r.get('note') or ''} (checked {B.dh(r['as_of'])})".strip()))
    out=dict(as_of=B.TODAY.isoformat(),as_of_h=B.dh(B.TODAY),rows=rows)
    json.dump(out,open(os.path.join(B.DIST,'ask-data.json'),'w'),separators=(',',':'))
    return len(rows)
