"""Daily price movers for Leaky Maple vs Golden Pour: each stock's % change from the session before to the last
completed session close. Free, no key: Yahoo Finance's public chart endpoint (unofficial; for personal/non-commercial
use under Yahoo's terms, so it's isolated here and easy to swap). Fetched once per build (~100 requests, throttled).
If the fetch fails, the last good copy in data/movers.json is used and its date is shown, so a stale price is never
passed off as today's."""
import json, os, time, datetime, urllib.request
UA={'User-Agent':'Mozilla/5.0 (MapleDividends build; mapledividends.com)'}
TSX_CLASS={'BIP':'BIP-UN','BEP':'BEP-UN','GIB':'GIB-A','GRT':'GRT-UN','QSP':'QSP-UN','RCI':'RCI-B','TECK':'TECK-B'}  # TSX share class / unit suffixes
def ysym(t,mkt): return (TSX_CLASS.get(t,t) if mkt=='TSX' else t).replace('.','-')+('.TO' if mkt=='TSX' else '')
def _one(sym,today):
    u=f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=10d&interval=1d"
    r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20))['chart']['result'][0]
    tz=r['meta'].get('exchangeTimezoneName','America/New_York')
    from zoneinfo import ZoneInfo
    rows=[(datetime.datetime.fromtimestamp(ts,ZoneInfo(tz)).date(),c) for ts,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if c is not None]
    rows=[x for x in rows if x[0]<today]  # completed sessions only (build runs before the open, PT)
    if len(rows)<2: return None
    (d0,c0),(d1,c1)=rows[-2],rows[-1]
    return dict(date=d1.isoformat(),close=round(c1,4),prev=round(c0,4),pct=round((c1/c0-1)*100,2),currency=r['meta'].get('currency'))
def fetch(items,mkt,today,root):
    """items: [dict(slug,ticker,name)]. Returns [dict(slug,ticker,name,date,close,prev,pct,currency)]."""
    path=os.path.join(root,'data','movers.json')
    try: cache=json.load(open(path))
    except (OSError,ValueError): cache={}
    out=[]
    if os.environ.get('MOVERS_OFFLINE')!='1':
        for it in items:
            try: q=_one(ysym(it['ticker'],mkt),today)
            except Exception: q=None
            if q: out.append(dict(slug=it['slug'],ticker=it['ticker'],name=it['name'],**q))
            time.sleep(0.25)
    if len(out)>=max(3,len(items)//2):  # good run: keep only the latest session, save it
        last=max(o['date'] for o in out); out=[o for o in out if o['date']==last]
        cache[mkt]=out
        try: json.dump(cache,open(path,'w'),indent=1)
        except OSError: pass
        return out
    return cache.get(mkt,[])
