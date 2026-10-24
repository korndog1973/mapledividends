"""Big TSX payers whose SEC filings word dividend declarations in ways parse.py's generic rules miss
(TD 'per fully paid common share ... payable on and after', Enbridge's DIVIDEND DECLARATION table, Fortis's bullet list,
Emera's numbered list, CN's spelled-out cents). Each ticker gets ONE exact sentence pattern taken from its own filings;
a declaration is kept only if that pattern matches and parse.checks() passes. Nothing is estimated.
Reads the cached EDGAR exhibits (data/manifest.json + a few extra EDGAR full-text searches) and fills data/parsed.json
for these tickers only when parse.py found no verified regular dividend for them."""
import json, os, re, sys, datetime, hashlib, subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import parse, fetch_edgar
ROOT=parse.ROOT; DATE=parse.DATE
# ticker -> (regex with named groups amt/rec/pay, currency, extra EDGAR full-text queries)
PAT={
 'TD':(rf'\(\$(?P<amt>\d+\.\d+)\)\s+per fully paid common share[^.]{{0,200}}?payable on and after (?P<pay>{DATE}),? to shareholders of record at the close of business on (?P<rec>{DATE})','CAD',[]),
 'ENB':(rf'(?:dividends are payable|payable) on (?P<pay>{DATE}),? to shareholders of record on (?P<rec>{DATE})\.?\s*(?:Dividend per share\s*)?Common Shares\s*\$\s?(?P<amt>\d+\.\d+)','CAD',['"DIVIDEND DECLARATION" "Common Shares"']),
 'CNR':(rf'quarterly dividend of [^()]{{0,80}}\(C\$(?P<amt>\d+\.\d+)\) per common share will be paid on (?P<pay>{DATE}),? to shareholders of record at the close of business on (?P<rec>{DATE})','CAD',[]),
 'FTS':(rf'declared the following dividends payable on (?P<pay>{DATE}) to the Shareholders of Record[^:]{{0,120}}? on (?P<rec>{DATE}):[^:]{{0,1500}}?\$(?P<amt>\d+\.\d+) per share on the Common Shares','CAD',['"per share on the Common Shares"']),
 'EMA':(rf'payable on and after (?P<pay>{DATE}),? to the applicable shareholders of record at the close of business on (?P<rec>{DATE}),? as follows: 1\. \$(?P<amt>\d+\.\d+) per common share','CAD',['"Declares Quarterly Dividends"']),
}
def text_of(url):
    b=fetch_edgar.get(url)
    if url.lower().endswith('.pdf'):
        p=os.path.join(fetch_edgar.CACHE,hashlib.sha1(url.encode()).hexdigest())
        return re.sub(r'\s+',' ',subprocess.run(['pdftotext',p,'-'],capture_output=True,timeout=60).stdout.decode('utf-8','ignore'))
    return re.sub(r'\s+',' ',parse.to_text(b))
def main():
    man=json.load(open(os.path.join(ROOT,'data','manifest.json')))
    uni={u['ticker']:u for u in json.load(open(os.path.join(ROOT,'data','universe.json')))}
    pp=os.path.join(ROOT,'data','parsed.json'); parsed=json.load(open(pp))
    added=[]
    for t,(pat,cur,qs) in PAT.items():
        if t not in uni or (parsed.get(t) or {}).get('regular'): continue
        docs={m['url']:(m['file_date'],m['form']) for m in man if m['ticker']==t}
        for q in qs:
            try:
                for h in fetch_edgar.search(uni[t]['cik'],q):
                    s=h['_source']; adsh,fn=h['_id'].split(':',1)
                    docs.setdefault(f"https://www.sec.gov/Archives/edgar/data/{uni[t]['cik']}/{adsh.replace('-','')}/{fn}",(s.get('file_date'),s.get('form') or (s.get('root_forms') or [''])[0]))
            except Exception as e: print('search fail',t,e,file=sys.stderr)
        rows={}
        for url,(fd,form) in sorted(docs.items(),key=lambda kv:kv[1][0]):
            try: txt=text_of(url)
            except Exception as e: print('doc fail',url,e,file=sys.stderr); continue
            fdd=datetime.date.fromisoformat(fd)
            for m in re.finditer(pat,txt,re.I):
                rec,pay=parse.pdate(m.group('rec')),parse.pdate(m.group('pay')); amt=float(m.group('amt'))
                d=dict(amount=amt,currency=cur,currency_basis=('amount' if 'C\\$' in pat else 'override'),record=rec,pay=pay,tight=True,frequency_kw=('Quarterly' if re.search(r'quarter',txt[max(0,m.start()-400):m.end()+100],re.I) else None),
                       special=False,special_strong=False,increase_kw=False,decrease_kw=False,drip_kw=False,drip_disc=None,snippet=txt[max(0,m.start()-200):m.end()+60][:500])
                d['errors']=parse.checks(d,fdd,form); d['verified']=not d['errors']
                if not d['verified']: continue
                k=(rec.isoformat(),amt)
                if k in rows: rows[k]['support']+=1; continue  # keep the earliest filing that announced it
                d.update(ticker=t,source=url,file_date=fd,form=form,first_filed=fd,support=1,tight_support=1,record=rec.isoformat(),pay=pay.isoformat())
                rows[k]=d
        regs=sorted(rows.values(),key=lambda d:d['record'],reverse=True)
        # one amount per record date, or we don't publish that date
        byrec={}
        for d in regs: byrec.setdefault(d['record'],[]).append(d)
        regs=[v[0] for v in byrec.values() if len(v)==1]
        if not regs: print('bigpayers: no verified declaration for',t); continue
        parsed[t]=dict(ticker=t,name=uni[t]['name'],composite=uni[t].get('composite',False),regular=regs,special=[],ambiguous=sorted(r for r,v in byrec.items() if len(v)>1),
                       unverified_count=0,unverified_errors=[],source_rule='bigpayers')
        added.append((t,len(regs)))
    json.dump(parsed,open(pp,'w'),indent=1)
    print('bigpayers added:',added)
if __name__=='__main__': main()
