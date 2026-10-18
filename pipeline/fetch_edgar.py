"""Fetch candidate dividend-declaration documents from SEC EDGAR (public domain).
Uses EDGAR full-text search per CIK, then downloads the matching exhibits. Polite: <=8 req/s, declared User-Agent.
Cache: pipeline/cache/ (safe to keep between runs)."""
import json, os, time, urllib.request, urllib.parse, hashlib, datetime, sys, threading
from concurrent.futures import ThreadPoolExecutor
LOCK=threading.Lock()
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA=os.environ.get("SEC_UA","MapleDividends admin@mapledividends.com")
CACHE=os.path.join(ROOT,'pipeline','cache'); os.makedirs(CACHE,exist_ok=True)
START=os.environ.get("START","2025-07-01"); END=datetime.date.today().isoformat()
MAXDOCS=int(os.environ.get("MAXDOCS","14"))
# DATASET=us: the Stars & Syrup U.S. set (data/us_universe.json -> data/us_manifest.json, 8-K/10-Q/10-K). Default: TSX set.
DATASET=os.environ.get("DATASET",""); PFX=DATASET+'_' if DATASET else ''
FORMS='8-K,10-Q,10-K' if DATASET=='us' else '6-K,8-K'  # many U.S. issuers only state record/pay dates in 10-Q/10-K
last=[0.0]
def get(url,binary=False,ttl=None):
    k=os.path.join(CACHE,hashlib.sha1(url.encode()).hexdigest())
    if os.path.exists(k) and (ttl is None or time.time()-os.path.getmtime(k)<ttl):
        return open(k,'rb').read()
    with LOCK:
        wait=0.13-(time.time()-last[0])
        if wait>0: time.sleep(wait)
        last[0]=time.time()
    for i in range(3):
        try:
            b=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"}),timeout=40).read(); break
        except Exception as e:
            if i==2: raise
            time.sleep(2*(i+1))
    open(k,'wb').write(b); return b
def search(cik,q):
    u="https://efts.sec.gov/LATEST/search-index?"+urllib.parse.urlencode(dict(q=q,ciks=str(cik).zfill(10),dateRange='custom',startdt=START,enddt=END,forms=FORMS))
    return json.loads(get(u,ttl=6*3600)).get('hits',{}).get('hits',[])
def main():
    uni=json.load(open(os.path.join(ROOT,'data',PFX+'universe.json')))
    manifest=[]
    def one(arg):
        n,c=arg
        hits={}
        for q in ['dividend "of record"','distribution "of record"','dividend payable record','"per common share" dividend payable']:
            for cik in c.get('ciks') or [c['cik']]:  # a company can have several CIKs (e.g. a new holding company)
              try:
                for h in search(cik,q): hits[h['_id']]=h['_source']
              except Exception as e: print("search fail",c['ticker'],e,file=sys.stderr)
        docs=sorted(hits.items(),key=lambda kv:kv[1].get('file_date',''),reverse=True)[:MAXDOCS]
        for _id,s in docs:
            adsh,fn=_id.split(':',1)
            fc=[int(x) for x in s.get('ciks') or []]; cik=next((x for x in (c.get('ciks') or [c['cik']]) if x in fc),c['cik'])
            url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-','')}/{fn}"
            try:
                get(url)
                manifest.append(dict(ticker=c['ticker'],cik=cik,url=url,file_date=s.get('file_date'),form=s.get('form') or (s.get('root_forms') or [''])[0],cache=hashlib.sha1(url.encode()).hexdigest()))
            except Exception as e: print("doc fail",url,e,file=sys.stderr)
        if n%20==0: print(n,c['ticker'],len(docs),flush=True)
    with ThreadPoolExecutor(int(os.environ.get("WORKERS","12"))) as ex: list(ex.map(one,enumerate(uni)))
    json.dump(manifest,open(os.path.join(ROOT,'data',PFX+'manifest.json'),'w'),indent=1)
    print("docs:",len(manifest))
if __name__=='__main__': main()
