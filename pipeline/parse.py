"""Parse cached EDGAR exhibits into dividend declarations, with sanity checks.
Only declarations that pass every check are marked verified=True. Never guesses missing fields."""
import json, os, re, html, datetime, collections, subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE=os.path.join(ROOT,'pipeline','cache')
# DATASET=us: Stars & Syrup U.S. set (data/us_manifest.json -> data/us_parsed.json). Default: TSX set.
DATASET=os.environ.get('DATASET',''); PFX=DATASET+'_' if DATASET else ''
MON='(?:January|February|March|April|May|June|July|August|September|October|November|December|(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\\.)'
DATE=rf'({MON}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}})'
def pdate(s):
    s=re.sub(r'(\d)(st|nd|rd|th)',r'\1',s).replace(',','')
    s=' '.join(s.split()).replace('Sept.','Sep.').replace('.','')
    for f in ('%B %d %Y','%b %d %Y'):
        try: return datetime.datetime.strptime(s,f).date()
        except ValueError: pass
    return None
def to_text(b):
    s=b.decode('utf-8','ignore')
    s=re.sub(r'(?is)<(script|style).*?</\1>',' ',s)
    s=re.sub(r'[\r\n]+',' ',s)  # raw source line breaks are insignificant in HTML; only block tags end a line
    s=re.sub(r'(?i)<br\s*/?>|</p>|</div>|</tr>|</td>',' . ',s) if False else re.sub(r'(?i)<br\s*/?>|</p>|</div>|</tr>',' \n ',s)
    s=re.sub(r'<[^>]+>',' ',s); s=html.unescape(s).replace('\xa0',' ')
    s=re.sub(r'[ \t\r\f\v]+',' ',s)
    # re-join sentences that were split across one-line-per-<div> layouts ("payable on March 16, \n 2026 to holders of record on \n February 27")
    s=re.sub(r'(?<=,) ?\n ?(?=[A-Za-z0-9(])|(?<=[a-z]) ?\n ?(?=[a-z0-9(])',' ',s)
    return re.sub(r'(?i)\b(on|of|to|at|as|the|and|or|per|in|by|for|from|with|before|after|about|a|an|share|shares) ?\n ?(?=[A-Za-z0-9($])',r'\1 ',s)
AMT=re.compile(r'(US\s?\$|U\.S\.\s?\$|USD\s?\$?|C\$|CDN\s?\$|Cdn\.?\s?\$|CAD\s?\$?|\$)\s?(\d{1,2}(?:\.\d{1,6})?)\s*(\(US\)|\(U\.S\.\)|US|U\.S\.|USD|\(CAD\)|\(Cdn\.?\)|CAD|Canadian|CDN|Cdn\.?)?\s*(?:(?:per|a|for each|on each)\s+(?:[A-Za-z\-]+\s+){0,5}?|/\s?)(share|unit|ADS)s?\b',re.I)
CENTS=re.compile(r'(\d{1,3}(?:\.\d{1,4})?)\s*cents?\s*(?:\(\$?0?\.\d+\)\s*)?(?:per|a|for each|on each)\s+(?:[A-Za-z\-]+\s+){0,5}?(share|unit)s?\b',re.I)
BAD=re.compile(r'preferred|preference|series\s+[a-z0-9]{1,3}\b|debenture|notes?\b|warrant|exchangeable|subscription receipt',re.I)
REC=[re.compile(rf'(?:of\s+record|record\s+date|holders\s+of\s+record)[^.;\n]{{0,90}}?{DATE}',re.I), re.compile(rf'{DATE}[^.;\n]{{0,40}}?record\s+date',re.I)]
PAY=[re.compile(rf'of\s+record[^.;\n]{{0,60}}?{DATE},?\s+(?:on|payable\s+on)\s+{DATE}',re.I), re.compile(rf'(?:payable|paid|payment\s+date|to\s+be\s+paid|pay\s+date)(?:(?!record)[^.;\n]){{0,70}}?{DATE}',re.I), re.compile(rf'on\s+or\s+(?:about|before)\s+{DATE}',re.I)]
REF=re.compile(r'increase of|increased by|increase from|compar|earlier|prior|previous|annuali[sz]|from\s*$|from \$|up from|were\s*\$?$|was\s*\$?$|totall?ing|aggregat|target|reset|paid during|paid quarterly dividends|in 20\d\d to|last quarter')
POST_REF=re.compile(r'^[^.;$]{0,20}?\b(?:annuali[sz]ed|annual\s+basis|per\s+annum|per\s+year|annually|for\s+the\s+(?:\d{4}\s+)?(?:fiscal\s+)?year|for\s+(?:fiscal\s+)?\d{4})\b|^\s*(?:annuali[sz]ed\s+)?(?:increase|decrease)\b',re.I)
DECL=re.compile(r'declar|approv|announc|confirm|set|authoriz|\bis\s+payable|will\s+be\s+paid|to\s+be\s+paid',re.I)
def freq_kw(w):
    w=w.lower()
    if re.search(r'semi-?\s?annual',w): return 'Semi-annual'
    if re.search(r'\bquarterly\b|for the (first|second|third|fourth) quarter|\bq[1-4] 20\d\d dividend',w): return 'Quarterly'
    if re.search(r'\bmonthly\b',w): return 'Monthly'
    if re.search(r'\bannual (cash )?dividend\b',w): return 'Annual'
    return None
USD_RE=re.compile(r'US\$|U\.S\.\s?\$|U\.S\.\s+dollars?|\bUS\s+dollars?|\bUSD\b|United\s+States\s+dollars?',re.I)
CAD_RE=re.compile(r'C\$|CDN\$|\bCAD\b|Canadian\s+dollars?|Cdn\.?\s+dollars?',re.I)
def currency(w):
    """Currency stated in a short excerpt, or None. Returns None when both are mentioned (can't tell which applies)."""
    # "The Canadian dollar equivalent ..." means the amount itself is in US dollars (and vice versa)
    eq_c=bool(re.search(r'Canadian\s+dollar\s+equivalent|equivalent\s+in\s+Canadian\s+dollars',w,re.I)); eq_u=bool(re.search(r'U\.?S\.?\s+dollar\s+equivalent|equivalent\s+in\s+U\.?S\.?\s+dollars',w,re.I))
    if eq_c!=eq_u: return 'USD' if eq_c else 'CAD'
    u=bool(USD_RE.search(w)); c=bool(CAD_RE.search(w))
    if u and not c: return 'USD'
    if c and not u: return 'CAD'
    return None
DOC_CUR=re.compile(r'\ball\s+(?:\w+\s+){0,3}?(?:amounts?|figures?|dollars?|financial\s+(?:figures|information|data|results)|results|references\s+to\s+[“"]?\$[”"]?(?:\s+or\s+[“"]?dollars[”"]?)?|currency)\b[^.;]{0,50}?\b(?:are|is|in|expressed|presented|reported|stated|refer|shown)\b(?:\s+(?:in|to|are|as|millions\s+of|thousands\s+of))*\s+(U\.S\.\s+dollars|US\s+dollars|United\s+States\s+dollars|Canadian\s+dollars|USD\b|CAD\b)',re.I)
def doc_currency(text):
    """Filing-wide reporting currency stated explicitly (e.g. 'All amounts in U.S. dollars unless otherwise noted'), or None."""
    found=set()
    for m in DOC_CUR.finditer(text[:60000]):
        g=m.group(1).lower(); found.add('CAD' if 'canad' in g or g.startswith('cad') else 'USD')
    return found.pop() if len(found)==1 else None
# --- U.S. set only (DATASET=us): wording U.S. issuers use that the TSX rules don't cover. Never applied to the TSX set.
US=DATASET=='us'
US_PAY=[re.compile(rf'payment\s+of\s+the\s+{DATE}\s+dividend',re.I)]  # IBM: "With payment of the September 10, 2026 dividend"
US_NEWRATE=re.compile(r'from\s+\$\s?\d+(?:\.\d+)?(?:\s+per\s+(?:common\s+)?share)?\s+to\s*$',re.I)  # "from $1.30 per share to [$1.34 per share]"
US_ANNUAL=re.compile(r'\bannual\s+(?:dividend|rate)\s+(?:rate\s+)?(?:of\s+)?$|equates\s+to\s+(?:an?\s+)?annual',re.I)  # "equates to an annual dividend of [$9.32]"
US_COMMON_AFTER=re.compile(r'^\s*on\s+(?:the\s+|its\s+|each\s+)?(?:outstanding\s+)?(?:shares?\s+of\s+)?(?:the\s+company.s\s+)?common',re.I)  # "$1.0885 per share on the Common Stock and on the ... Preferred"
def us_normalize(text,file_date):
    """'5:00 p.m.' -> '5:00 pm' (the dot ends the date window); add the year to year-less dates ('payable Dec. 15'),
    choosing the year that puts the date closest after the filing (from 30 days before to 335 days after)."""
    text=re.sub(r'(\d)\s*([ap])\.m\.',r'\1 \2m',text,flags=re.I)
    def addyear(m):
        for y in (file_date.year-1,file_date.year,file_date.year+1):
            d=pdate(f"{m.group(0)} {y}")
            if d and file_date-datetime.timedelta(days=30)<=d<=file_date+datetime.timedelta(days=335): return f"{m.group(0)}, {y}"
        return m.group(0)
    return re.sub(rf'{MON}\s+\d{{1,2}}(?:st|nd|rd|th)?\b(?!\s*,?\s*\d{{4}})(?!\s*,?\s*\d)',addyear,text)
def _row(amt,rec,pay,sn,kw='Quarterly'):
    return dict(amount=round(amt,6),currency=None,currency_basis=None,record=rec,pay=pay,tight=True,frequency_kw=kw,special=False,special_strong=False,
                increase_kw=False,decrease_kw=False,drip_kw=False,drip_disc=None,snippet=sn[:500])
US_TBL_MSFT=re.compile(r'Declaration\s+Date\s+Record\s+Date\s+Payment\s+Date\s+Dividend\s+Per\s+Share\s+Amount(.{0,6000}?)(?=\bTotal\b|We\s+returned|Refer\s+to|$)',re.I|re.S)
US_TBL_ROW=re.compile(rf'{DATE}\s+{DATE}\s+{DATE}\s+(?:\$\s*)?(\d{{1,2}}\.\d{{2,4}})\s+(?:\$\s*)?[\d,]+')
US_TBL_WMT=re.compile(rf'installments\s+of\s+\$\s?(\d{{1,2}}\.\d{{2,4}})\s+per\s+share,?\s+according\s+to\s+the\s+following\s+record\s+and\s+payable\s+dates:?\s+Record\s+Date\s+Payable\s+Date\s+((?:{DATE}\s+{DATE}\s*){{1,6}})',re.I)
def us_tables(text):
    """Dividend tables some U.S. issuers use instead of sentences (U.S. set only):
    Microsoft 10-Q/10-K 'Declaration Date | Record Date | Payment Date | Dividend Per Share | Amount';
    Walmart 'installments of $X per share, according to the following record and payable dates: Record Date Payable Date ...'."""
    out=[]
    for t in US_TBL_MSFT.finditer(text):
        for r in US_TBL_ROW.finditer(re.sub(r'\s+',' ',t.group(1))):
            out.append(_row(float(r.group(4)),pdate(r.group(2)),pdate(r.group(3)),'Declaration Date / Record Date / Payment Date / Dividend Per Share: '+' | '.join(r.groups())))
    for t in US_TBL_WMT.finditer(text):
        ds=[pdate(x) for x in re.findall(DATE,t.group(2))]
        for rec,pay in zip(ds[0::2],ds[1::2]):
            out.append(_row(float(t.group(1)),rec,pay,f"Quarterly installment of ${t.group(1)} per share: record date {rec}, payable {pay} (from the filing's record and payable dates table)"))
    return out
SENT_END=re.compile(r'(?<!\b[A-Z])(?<!\bInc)(?<!\bNo)(?<!\bCo)\.\s*(?=[A-Z(])|\n|\$\s?\d|\d\s*cents')
def parse_doc(text,file_date):
    out=[]
    for m in list(AMT.finditer(text))+list(CENTS.finditer(text)):
        s=max(0,m.start()-350); e=min(len(text),m.end()+450)
        w=text[s:e]
        near=text[max(0,m.start()-160):m.end()+40]
        if not re.search(r'dividend|distribution',near,re.I): continue
        if not DECL.search(near): continue
        # other securities (preferred shares, notes...): an explicit "per common share" wins over a mention nearby
        if BAD.search(m.group(0)): continue
        if not re.search(r'\bcommon\b|\bclass\s+[a-z]\b(?!\s+preferred)',m.group(0),re.I) and BAD.search(near) and not (US and US_COMMON_AFTER.search(text[m.end():m.end()+60])): continue
        pre=text[max(0,m.start()-70):m.start()].lower()
        if US and US_ANNUAL.search(pre): continue
        if REF.search(pre) and not (US and US_NEWRATE.search(pre)): continue
        if POST_REF.search(text[m.end():m.end()+40]): continue  # e.g. "$0.24 per share annualized increase", "$0.08 per share on an annualized basis"
        cur_basis=None
        if m.re is CENTS:
            amt=float(m.group(1))/100; cur=currency(near); cur_basis='excerpt' if cur else None
        else:
            amt=float(m.group(2)); g=m.group(1).upper(); suf=(m.group(3) or '').upper()
            if g.startswith(('US','U.S')) or suf.strip('()').startswith(('US','U.S')): cur,cur_basis='USD','amount'
            elif g.startswith(('C$','CDN','CAD')) or suf.strip('().').startswith(('CAD','CANADIAN','CDN')): cur,cur_basis='CAD','amount'
            else:
                cur=currency(text[max(0,m.start()-120):m.end()+120]); cur_basis='excerpt' if cur else None
        tail=text[m.start():e]
        # the clause that belongs to this amount: up to the end of the sentence or the next amount
        after=re.sub(r'\([^()]{0,200}\)',lambda x:' '*len(x.group(0)),text[m.end():e])  # ignore parentheticals like "(or $0.08 annualized)"
        cl_end=SENT_END.search(after); clause=text[m.start():m.end()+(cl_end.start() if cl_end else len(after))]
        def find(pats):
            for r in pats:  # same sentence as the amount first
                x=r.search(clause)
                if x: return pdate(x.group(x.lastindex)),True
            for r in pats:  # then the surrounding text
                x=r.search(tail) or r.search(w)
                if x: return pdate(x.group(x.lastindex)),False
            return None,False
        rec,tight_r=find(REC); pay,tight_p=find(PAY+US_PAY if US else PAY)
        SPEC=r'special|extra|one-time|supplemental|variable|performance\s+(?:dividend|top-up)|in\s+respect\s+of\s+performance|top-up|return of capital distribution'
        special=bool(re.search(SPEC,near,re.I))
        special_strong=bool(re.search(SPEC,text[max(0,m.start()-30):m.start()]+' '+clause,re.I))  # tied to this amount, not just nearby
        sent=re.sub(r'\s+',' ',text[max(0,m.start()-200):m.end()+250]).strip()
        wide=text[max(0,m.start()-160):m.end()+250]
        out.append(dict(amount=round(amt,6),currency=cur,currency_basis=cur_basis,record=rec,pay=pay,tight=tight_r and tight_p,frequency_kw=freq_kw(near),special=special,special_strong=special_strong,
                        increase_kw=bool(re.search(r'increas|rais',wide,re.I)),decrease_kw=bool(re.search(r'reduc|decreas|\bcut\b|\breset\b',wide,re.I)),
                        drip_kw=bool(re.search(r'reinvestment plan|\bDRIP\b',w)),
                        drip_disc=(lambda d: d.group(1) if d else None)(re.search(r'(\d(?:\.\d+)?)\s?%\s+discount',w,re.I)),
                        snippet=sent[:500]))
    return out
def checks(d,file_date,form=''):
    errs=[]
    # periodic reports (U.S. set) describe declarations made during the quarter, so the record date can precede the filing by months
    back=200 if US and form in ('10-Q','10-K') else 10
    if not (0.0001<=d['amount']<=25): errs.append('amount out of range')
    if not d['record']: errs.append('no record date')
    if not d['pay']: errs.append('no pay date')
    if d['record'] and not (file_date-datetime.timedelta(days=back)<=d['record']<=file_date+datetime.timedelta(days=150)): errs.append('record date far from filing date')
    if d['record'] and d['pay'] and not (d['record']<d['pay']<=d['record']+datetime.timedelta(days=120)): errs.append('pay date inconsistent with record date')
    return errs
def main():
    man=json.load(open(os.path.join(ROOT,'data',PFX+'manifest.json')))
    uni={u['ticker']:u for u in json.load(open(os.path.join(ROOT,'data',PFX+'universe.json')))}
    allrows=[]
    for m in man:
        p=os.path.join(CACHE,m['cache'])
        if not os.path.exists(p): continue
        fd=datetime.date.fromisoformat(m['file_date'])
        if m['url'].lower().endswith('.pdf'):
            try: txt=subprocess.run(['pdftotext',p,'-'],capture_output=True,timeout=60).stdout.decode('utf-8','ignore'); txt=re.sub(r'\s+',' ',txt)
            except Exception: continue
        else: txt=to_text(open(p,'rb').read())
        if US: txt=us_normalize(txt,fd)
        dcur=doc_currency(txt)
        for d in parse_doc(txt,fd)+(us_tables(txt) if US else []):
            if not d['currency'] and dcur: d['currency'],d['currency_basis']=dcur,'filing'
            d['errors']=checks(d,fd,m['form']); d['verified']=not d['errors']
            d.update(ticker=m['ticker'],source=m['url'],file_date=m['file_date'],form=m['form'])
            allrows.append(d)
    # if a filing explicitly calls an amount special/performance, every mention of that amount in that filing is special
    spec={(d['ticker'],d['source'],d['amount']) for d in allrows if d['special_strong']}
    for d in allrows:
        if (d['ticker'],d['source'],d['amount']) in spec: d['special']=True
    # dedupe per ticker by (record,amount)
    by=collections.defaultdict(dict); sup=collections.Counter(); tsup=collections.Counter()
    agg=collections.defaultdict(lambda: dict(inc=False,dec=False,curs=collections.Counter(),first=None))
    for d in allrows:
        k=(d['record'],d['amount'],d['special'])
        cur=by[d['ticker']].get(k)
        sup[(d['ticker'],k)]+=1 if d['verified'] else 0
        tsup[(d['ticker'],k)]+=1 if (d['verified'] and d['tight']) else 0
        if d['verified']:
            a=agg[(d['ticker'],k)]; a['inc']|=d['increase_kw']; a['dec']|=d['decrease_kw']
            a['first']=min(a['first'] or d['file_date'],d['file_date'])
            if d['currency']: a['curs'][(d['currency'],d['currency_basis'])]+=1
        if cur is None or (d['verified'] and not cur['verified']) or (d['verified']==cur['verified'] and (d['tight'],d['file_date']<cur['file_date'])>(cur['tight'],False)): by[d['ticker']][k]=d
    # currency: per declaration, the most direct statement across all filings reporting it; then manual overrides; then the company's own consistent filings
    overrides={k:v for k,v in json.load(open(os.path.join(ROOT,'data','currency_overrides.json'))).items() if not k.startswith('_')}
    RANK={'amount':0,'excerpt':1,'filing':2}
    for (t,k),a in agg.items():
        d=by[t][k]
        d['increase_kw']=a['inc']; d['decrease_kw']=a['dec']; d['first_filed']=a['first']
        if not a['curs']: continue
        best=min(RANK[b] for (_,b) in a['curs'])
        cands={c for (c,b) in a['curs'] if RANK[b]==best}
        if len(cands)==1: d['currency']=cands.pop(); d['currency_basis']=[b for b in RANK if RANK[b]==best][0]
        else: d['currency']=None; d['currency_basis']='conflict'
        d['increase_kw']=a['inc']; d['decrease_kw']=a['dec']; d['first_filed']=a['first']
    excl=json.load(open(os.path.join(ROOT,'pipeline','exclusions.json')))
    companies={}
    for t,dd in by.items():
        if t in excl: continue
        ver=sorted([d for d in dd.values() if d['verified']],key=lambda d:(d['record'],d['file_date']),reverse=True)
        unv=[d for d in dd.values() if not d['verified']]
        # if one record date has several regular amounts (e.g. share classes), keep them but flag ambiguity
        regs=[d for d in ver if not d['special']]
        for d in regs:
            k=(d['record'],d['amount'],d['special']); d['support']=sup[(t,k)]; d['tight_support']=tsup[(t,k)]
        bydate=collections.defaultdict(list)
        for d in regs: bydate[d['record']].append(d)
        clean=[]; ambiguous=set()
        for r,lst in bydate.items():
            # Prefer amounts whose record AND pay dates are stated in the same sentence as the amount
            # (a declaration), over amounts that merely sit near those dates (e.g. MD&A tables of past dividends).
            if any(d['tight_support'] for d in lst): lst=[d for d in lst if d['tight_support']]; key='tight_support'
            else: key='support'
            lst.sort(key=lambda d:-d[key])
            if len(lst)==1 or lst[0][key]>=2*lst[1][key]: clean.append(lst[0])
            else: ambiguous.add(r)
        # currency fallbacks for declarations whose filings don't state it
        ov=overrides.get(t)
        known={d['currency'] for d in clean if d['currency'] and d['currency_basis'] in ('amount','excerpt','filing')}
        for d in clean+[d for d in ver if d['special']]:
            if ov and (d.get('currency_basis') in (None,'conflict') or (d.get('currency_basis')=='filing' and d['currency']!=ov['currency'])): d['currency'],d['currency_basis']=ov['currency'],'override'; continue
            if d['currency']: continue
            if len(known)==1 and d.get('currency_basis')!='conflict': d['currency'],d['currency_basis']=next(iter(known)),'company'
        clean.sort(key=lambda d:(d['record'],d['file_date']),reverse=True)
        companies[t]=dict(ticker=t,name=uni[t]['name'],composite=uni[t].get('composite',False),
                          regular=clean,special=[d for d in ver if d['special']],ambiguous=sorted(str(a) for a in ambiguous),
                          unverified_count=len(unv),unverified_errors=collections.Counter(e for d in unv for e in d['errors']).most_common(3))
    def ser(o):
        if isinstance(o,datetime.date): return o.isoformat()
        raise TypeError
    json.dump(companies,open(os.path.join(ROOT,'data',PFX+'parsed.json'),'w'),indent=1,default=ser)
    n=sum(1 for c in companies.values() if c['regular'])
    print("companies with docs:",len(companies),"| with >=1 verified regular declaration:",n)
if __name__=='__main__': main()
