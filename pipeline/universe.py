"""Build the internal company universe: TSX operating companies that file with SEC EDGAR.
Input: TSX issuer list (internal use only, never published) + SEC company_tickers_exchange.json.
Output: data/universe.json  [{ticker, name, cik, composite}]"""
import json, re, os, urllib.request, openpyxl
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA=os.environ.get("SEC_UA","MapleDividends admin@mapledividends.com")
def norm(n):
    n=n.lower().replace('&',' and ')
    n=re.sub(r'/[a-z]+/','',n)
    n=re.sub(r'\b(inc|corp|corporation|ltd|limited|the|co|company|plc|lp|l\.p|trust|incorporated|ltee|ltée|sa|s\.a)\b\.?','',n)
    return ' '.join(re.sub(r'[^a-z0-9 ]',' ',n).split())
def main():
    p=os.path.join(ROOT,'pipeline','sec_tickers.json')
    if not os.path.exists(p) or os.environ.get('REFRESH'):
        open(p,'wb').write(urllib.request.urlopen(urllib.request.Request("https://www.sec.gov/files/company_tickers_exchange.json",headers={"User-Agent":UA}),timeout=60).read())
    sec=json.load(open(p)); f=sec['fields']; d=[dict(zip(f,x)) for x in sec['data']]
    byname={}; bytick={}
    for x in d:
        byname.setdefault(norm(x['name']),x); bytick.setdefault((x['ticker'] or '').upper(),[]).append(x)
    wb=openpyxl.load_workbook(os.path.join(ROOT,'pipeline','issuers_2026-08.xlsx'),read_only=True)
    rows=list(wb.worksheets[0].iter_rows(values_only=True)); data=[r for r in rows[10:] if r[0]]
    EX={'ETP','CDR','Closed-End Funds','SPAC'}
    out=[]
    for r in data:
        if r[8] in EX: continue
        tk, name = r[3], r[2]; n=norm(name); hit=None
        if n in byname: hit=byname[n]
        else:
            for x in bytick.get(tk.upper(),[]):
                a=set(norm(x['name']).split()); b=set(n.split())
                if a and b and len(a&b)/max(1,min(len(a),len(b)))>=0.5: hit=x;break
        if hit: out.append(dict(ticker=tk,name=name,cik=int(hit['cik']),composite=r[17] in ('Composite',60)))
    os.makedirs(os.path.join(ROOT,'data'),exist_ok=True)
    json.dump(out,open(os.path.join(ROOT,'data','universe.json'),'w'),indent=1)
    print("universe (TSX operating cos on EDGAR):",len(out),"composite:",sum(o['composite'] for o in out))
if __name__=='__main__': main()
