"""Parse cached EDGAR exhibits into dividend declarations, with sanity checks.
Only declarations that pass every check are marked verified=True. Never guesses missing fields."""
import json, os, re, html, datetime, collections, subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE=os.path.join(ROOT,'pipeline','cache')
MON='(?:January|February|March|April|May|June|July|August|September|October|November|December)'
DATE=rf'({MON}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}})'
def pdate(s):
    s=re.sub(r'(\d)(st|nd|rd|th)',r'\1',s).replace(',','')
    s=' '.join(s.split())
    try: return datetime.datetime.strptime(s,'%B %d %Y').date()
    except ValueError: return None
def to_text(b):
    s=b.decode('utf-8','ignore')
    s=re.sub(r'(?is)<(script|style).*?</\1>',' ',s)
    s=re.sub(r'(?i)<br\s*/?>|</p>|</div>|</tr>|</td>',' . ',s) if False else re.sub(r'(?i)<br\s*/?>|</p>|</div>|</tr>',' \n ',s)
    s=re.sub(r'<[^>]+>',' ',s); s=html.unescape(s).replace('\xa0',' ')
    return re.sub(r'[ \t\r\f\v]+',' ',s)
AMT=re.compile(r'(US\$|U\.S\.\s?\$|USD\s?\$?|C\$|CDN\$|CAD\s?\$?|\$)\s?(\d{1,2}(?:\.\d{1,6})?)\s*(?:\(US\)|US|U\.S\.|CAD|Canadian|CDN)?\s*(?:per|a|for each|on each)\s+(?:[A-Za-z\-]+\s+){0,5}?(share|unit|ADS)s?\b',re.I)
CENTS=re.compile(r'(\d{1,3}(?:\.\d{1,4})?)\s*cents?\s*(?:\(\$?0?\.\d+\)\s*)?(?:per|a|for each|on each)\s+(?:[A-Za-z\-]+\s+){0,5}?(share|unit)s?\b',re.I)
BAD=re.compile(r'preferred|preference|series\s+[a-z0-9]{1,3}\b|debenture|notes?\b|warrant|exchangeable|subscription receipt',re.I)
REC=[re.compile(rf'(?:of\s+record|record\s+date|holders\s+of\s+record)[^.;\n]{{0,90}}?{DATE}',re.I), re.compile(rf'{DATE}[^.;\n]{{0,40}}?record\s+date',re.I)]
PAY=[re.compile(rf'(?:payable|paid|payment\s+date|to\s+be\s+paid|pay\s+date)(?:(?!record)[^.;\n]){{0,70}}?{DATE}',re.I), re.compile(rf'on\s+or\s+(?:about|before)\s+{DATE}',re.I)]
REF=re.compile(r'increase of|increased by|increase from|compar|earlier|prior|previous|annuali[sz]|from\s*$|from \$|up from|were\s*\$?$|was\s*\$?$|totall?ing|reset|paid during|paid quarterly dividends|in 20\d\d to|last quarter')
DECL=re.compile(r'declar|approv|announc|confirm|set|authoriz',re.I)
def freq_kw(w):
    w=w.lower()
    if re.search(r'semi-?\s?annual',w): return 'Semi-annual'
    if re.search(r'\bquarterly\b|for the (first|second|third|fourth) quarter|\bq[1-4] 20\d\d dividend',w): return 'Quarterly'
    if re.search(r'\bmonthly\b',w): return 'Monthly'
    if re.search(r'\bannual (cash )?dividend\b',w): return 'Annual'
    return None
def currency(w):
    if re.search(r'US\$|U\.S\.\s?\$|U\.S\. dollars|\bUSD\b|United States dollars',w): return 'USD'
    if re.search(r'C\$|CDN\$|\bCAD\b|Canadian dollars',w): return 'CAD'
    return None
def parse_doc(text,file_date):
    out=[]
    for m in list(AMT.finditer(text))+list(CENTS.finditer(text)):
        s=max(0,m.start()-350); e=min(len(text),m.end()+450)
        w=text[s:e]
        near=text[max(0,m.start()-160):m.end()+40]
        if not re.search(r'dividend|distribution',near,re.I): continue
        if not DECL.search(near): continue
        if BAD.search(near): continue
        pre=text[max(0,m.start()-70):m.start()].lower()
        if REF.search(pre): continue
        if m.re is CENTS: amt=float(m.group(1))/100; cur=currency(near)
        else:
            amt=float(m.group(2)); g=m.group(1).upper()
            cur='USD' if g.startswith('US') or g.startswith('U.S') else ('CAD' if g.startswith(('C$','CDN','CAD')) else currency(near))
        tail=text[m.start():e]
        rec=None; pay=None
        for r in REC:
            x=r.search(tail) or r.search(w)
            if x: rec=pdate(x.group(1)); break
        for r in PAY:
            x=r.search(tail) or r.search(w)
            if x: pay=pdate(x.group(1)); break
        special=bool(re.search(r'special|extra|one-time|supplemental|variable|return of capital distribution',near,re.I))
        sent=re.sub(r'\s+',' ',text[max(0,m.start()-200):m.end()+250]).strip()
        out.append(dict(amount=round(amt,6),currency=cur,record=rec,pay=pay,frequency_kw=freq_kw(near),special=special,
                        increase_kw=bool(re.search(r'increas|rais',near,re.I)),decrease_kw=bool(re.search(r'reduc|decreas|\bcut\b',near,re.I)),
                        drip_kw=bool(re.search(r'reinvestment plan|\bDRIP\b',w)),
                        drip_disc=(lambda d: d.group(1) if d else None)(re.search(r'(\d(?:\.\d+)?)\s?%\s+discount',w,re.I)),
                        snippet=sent[:500]))
    return out
def checks(d,file_date):
    errs=[]
    if not (0.0001<=d['amount']<=25): errs.append('amount out of range')
    if not d['record']: errs.append('no record date')
    if not d['pay']: errs.append('no pay date')
    if d['record'] and not (file_date-datetime.timedelta(days=10)<=d['record']<=file_date+datetime.timedelta(days=150)): errs.append('record date far from filing date')
    if d['record'] and d['pay'] and not (d['record']<d['pay']<=d['record']+datetime.timedelta(days=120)): errs.append('pay date inconsistent with record date')
    return errs
def main():
    man=json.load(open(os.path.join(ROOT,'data','manifest.json')))
    uni={u['ticker']:u for u in json.load(open(os.path.join(ROOT,'data','universe.json')))}
    allrows=[]
    for m in man:
        p=os.path.join(CACHE,m['cache'])
        if not os.path.exists(p): continue
        fd=datetime.date.fromisoformat(m['file_date'])
        if m['url'].lower().endswith('.pdf'):
            try: txt=subprocess.run(['pdftotext',p,'-'],capture_output=True,timeout=60).stdout.decode('utf-8','ignore'); txt=re.sub(r'\s+',' ',txt)
            except Exception: continue
        else: txt=to_text(open(p,'rb').read())
        for d in parse_doc(txt,fd):
            d['errors']=checks(d,fd); d['verified']=not d['errors']
            d.update(ticker=m['ticker'],source=m['url'],file_date=m['file_date'],form=m['form'])
            allrows.append(d)
    # dedupe per ticker by (record,amount)
    by=collections.defaultdict(dict); sup=collections.Counter()
    for d in allrows:
        k=(d['record'],d['amount'],d['special'])
        cur=by[d['ticker']].get(k)
        sup[(d['ticker'],k)]+=1 if d['verified'] else 0
        if cur is None or (d['verified'] and not cur['verified']) or (d['verified']==cur['verified'] and d['file_date']<cur['file_date']): by[d['ticker']][k]=d
    excl=json.load(open(os.path.join(ROOT,'pipeline','exclusions.json')))
    companies={}
    for t,dd in by.items():
        if t in excl: continue
        ver=sorted([d for d in dd.values() if d['verified']],key=lambda d:(d['record'],d['file_date']),reverse=True)
        unv=[d for d in dd.values() if not d['verified']]
        # if one record date has several regular amounts (e.g. share classes), keep them but flag ambiguity
        regs=[d for d in ver if not d['special']]
        for d in regs: d['support']=sup[(t,(d['record'],d['amount'],d['special']))]
        bydate=collections.defaultdict(list)
        for d in regs: bydate[d['record']].append(d)
        clean=[]; ambiguous=set()
        for r,lst in bydate.items():
            lst.sort(key=lambda d:-d['support'])
            if len(lst)==1 or lst[0]['support']>=2*lst[1]['support']: clean.append(lst[0])
            else: ambiguous.add(r)
        clean.sort(key=lambda d:(d['record'],d['file_date']),reverse=True)
        companies[t]=dict(ticker=t,name=uni[t]['name'],composite=uni[t]['composite'],
                          regular=clean,special=[d for d in ver if d['special']],ambiguous=sorted(str(a) for a in ambiguous),
                          unverified_count=len(unv),unverified_errors=collections.Counter(e for d in unv for e in d['errors']).most_common(3))
    def ser(o):
        if isinstance(o,datetime.date): return o.isoformat()
        raise TypeError
    json.dump(companies,open(os.path.join(ROOT,'data','parsed.json'),'w'),indent=1,default=ser)
    n=sum(1 for c in companies.values() if c['regular'])
    print("companies with docs:",len(companies),"| with >=1 verified regular declaration:",n)
if __name__=='__main__': main()
