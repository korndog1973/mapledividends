"""Canadian Data Centre & AI Power Tracker (/power-grid/). Hand-curated rows in data/power_projects.json (each with
source_url and as_of), plus last-close price moves for the linked tickers via the same free Yahoo chart call as
movers.py. Prices are cached in data/power_prices.json; if a fetch fails the cached date is shown, never passed off as fresh."""
import json, os, time, collections
import movers
PATH='/power-grid/'
NAMES={'TA':'TransAlta','PPL':'Pembina Pipeline','CPX':'Capital Power','BCE':'BCE (Bell)','T':'TELUS','HIVE':'HIVE Digital',
       'BEP':'Brookfield Renewable','BAM':'Brookfield Asset Management','CCO':'Cameco','FTS':'Fortis',
       'META':'Meta Platforms','GOOGL':'Alphabet (Google)','MSFT':'Microsoft','BE':'Bloom Energy'}
def prices(B,tks):
    path=os.path.join(B.ROOT,'data','power_prices.json')
    try: cache=json.load(open(path))
    except (OSError,ValueError): cache={}
    if os.environ.get('MOVERS_OFFLINE')!='1':
        for t,m in tks:
            try: q=movers._one(movers.ysym(t,'TSX' if m=='TSX' else 'US'),B.TODAY)
            except Exception: q=None
            if q: cache[t]=q
            time.sleep(0.25)
        try: json.dump(cache,open(path,'w'),indent=1)
        except OSError: pass
    return cache
def build(B,common):
    p=os.path.join(B.ROOT,'data','power_projects.json')
    if not os.path.exists(p): return [],None
    rows=json.load(open(p))['rows']
    by=collections.OrderedDict()
    for r in rows:
        r['announced_h']=(B.dh(r['announced']) if r.get('announced') and len(r['announced'])==10 else (r.get('announced') or '—'))
        for t,m in r['tickers']: by.setdefault((t,m),[]).append(r['project'])
    q=prices(B,list(by))
    tickers=[]
    for (t,m),projs in by.items():
        x=q.get(t)
        tickers.append(dict(ticker=t,market=m,name=NAMES.get(t,t),n=len(projs),projects=projs,
            close_h=(('C$' if x['currency']=='CAD' else 'US$')+f"{x['close']:.2f}") if x else None,
            pct=x['pct'] if x else None,pct_h=((('\u2212' if x['pct']<0 else '+')+f"{abs(x['pct']):.1f}%") if x else None),
            date_h=B.dh(x['date']) if x else None))
    tickers.sort(key=lambda d:(-d['n'],d['ticker']))
    dates=sorted({d['date_h'] for d in tickers if d['date_h']})
    asof=max(r['as_of'] for r in rows)
    mw=sum(1 for r in rows if r['province'] in ('AB','BC','QC','ON','SK','MB','NS','NB'))
    B.write(PATH,B.env.get_template('power.html').render(
        title="Canadian Data Centre & AI Power Tracker: projects, MW and TSX stocks | MapleDividends",
        description=f"{len(rows)} data centre and AI power projects tied to Canadian-listed companies (TransAlta, Capital Power, Pembina, BCE, TELUS, Brookfield, Cameco, Fortis), with MW, status and sources.",
        path=PATH,rows=rows,tickers=tickers,price_date=', '.join(dates),asof_h=B.dh(asof),n_canada=mw,**common))
    return [PATH],dict(n=len(rows),n_canada=mw)
