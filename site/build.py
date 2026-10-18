"""Static site generator: data/parsed.json -> dist/ . Pure Python + Jinja2."""
import json, os, re, shutil, datetime, statistics, collections, sys
from jinja2 import Environment, FileSystemLoader, select_autoescape
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST=os.path.join(ROOT,'dist'); SITE_URL=os.environ.get('SITE_URL','https://mapledividends.com')
TODAY=datetime.date.fromisoformat(os.environ['BUILD_DATE']) if os.environ.get('BUILD_DATE') else datetime.date.today()
START=os.environ.get("START","2025-07-01")
# Cloudflare Web Analytics (free, cookieless). The beacon token is public (it ships in every page); paste it here or set
# the CF_BEACON_TOKEN repo variable. Empty = no beacon.
BEACON_TOKEN=os.environ.get('CF_BEACON_TOKEN') or ''
# IndexNow key (Bing/Yandex/etc.). The key file site/static/<key>.txt is published at /<key>.txt.
INDEXNOW_KEY='898225b7cda0c6da25d61f8790afcf9d'
# Broker referral links shown in the "Start investing" box (home + company pages). Empty string = that broker isn't shown;
# if both are empty the box and the referral wording on the disclosure pages disappear.
MOOMOO_REF_URL='https://j.moomoo.com/0KnjKO'   # Moomoo Canada referral (code J8U8DMTM)
WEALTHSIMPLE_REF_URL = 'https://wealthsimple.com/invite/4CAYHA'                        # paste Wealthsimple referral link here to show it
REFERRALS=[r for r in (
    dict(name='Moomoo',url=MOOMOO_REF_URL,blurb='Trading app for Canadian and U.S. stocks, with TFSA and RRSP accounts.'),
    dict(name='Wealthsimple',url=WEALTHSIMPLE_REF_URL,blurb='Canadian investing app with TFSA, RRSP and FHSA accounts.'),
) if r['url']]
env=Environment(loader=FileSystemLoader(os.path.join(ROOT,'site','templates')),autoescape=select_autoescape(['html']))
D=datetime.date.fromisoformat
def dh(d): d=D(d) if isinstance(d,str) else d; return d.strftime('%b %-d, %Y')
CUR_NOTE={'filing':"currency per the filing's general statement",'company':"currency per the company's other filings",'override':"currency from our company notes; this filing doesn't state it"}
def money(a,cur):
    s=f"{a:.6f}".rstrip('0'); s=s if len(s.split('.')[1])>=2 else f"{a:.2f}"
    return (f"US${s}" if cur=='USD' else f"C${s}" if cur=='CAD' else f"${s}")
def slug(t): return re.sub(r'[^a-z0-9]+','-',t.lower()).strip('-')
def unit_of(sn):
    s=sn.lower(); return 'unit' if re.search(r'per (?:trust |class [a-z] )?unit',s) else 'share'
def freq(c):
    regs=c['regular']; kw=regs[0].get('frequency_kw') if regs else None
    if kw: return kw
    ds=sorted(D(r['record']) for r in regs)
    if len(ds)>=3:
        g=statistics.median([(b-a).days for a,b in zip(ds,ds[1:])])
        for lo,hi,lab in [(25,35,'Monthly'),(80,100,'Quarterly'),(170,200,'Semi-annual'),(350,380,'Annual')]:
            if lo<=g<=hi: return lab
    return 'Not stated'
GAP={'Monthly':31,'Quarterly':91,'Semi-annual':182,'Annual':365}
def change(regs,fq=None):
    """Most recent change in the regular dividend: the FIRST declaration at the current rate vs the declaration before it.
    If the two are further apart than the payment frequency allows, a declaration is missing from our data, so we
    don't know when the change was announced (gap=True) and it is kept off the dated raises/cuts list."""
    if len(regs)<2: return dict(kind='none',label='No earlier dividend in our data',pct=None)
    last=[r['amount'] for r in regs[:4]]
    steps=[b-a for a,b in zip(last[1:],last)]  # newer minus older
    if len(last)>=3 and len(set(last))==len(last) and any(x>0 for x in steps) and any(x<0 for x in steps):
        return dict(kind='none',label='Amount changes every period (variable dividend), so we don\'t count it as a raise or cut',pct=None)
    i=1
    while i<len(regs) and abs(regs[i]['amount']-regs[0]['amount'])<1e-9: i+=1
    if i==len(regs): return dict(kind='same',label=f"Unchanged since {dh(regs[-1]['record'])} (start of our data)",pct=0)
    a,b=regs[i-1],regs[i]
    if a['currency'] and b['currency'] and a['currency']!=b['currency']: return dict(kind='none',label='Not comparable (currency)',pct=None)
    if b['amount']==0: return dict(kind='none',label='n/a',pct=None)
    p=(a['amount']-b['amount'])/b['amount']*100
    spacing=[(D(x['record'])-D(y['record'])).days for x,y in zip(regs,regs[1:])]
    g=GAP.get(fq) or (min(spacing) if len(spacing)>=2 else None)  # frequency not stated: use the tightest spacing we've seen
    days=(D(a['record'])-D(b['record'])).days
    gap=bool(g and days>1.6*g)
    first=a.get('first_filed') or a['file_date']
    base=dict(pct=p,decl=a,prev=b,first_filed=first,gap=gap)
    if abs(p)>50:
        sn=a.get('snippet','').lower()
        ok=(a.get('decrease_kw') or re.search(r'reset|reduc|\bcut\b|decreas',sn)) if p<0 else (a.get('increase_kw') or re.search(r'increas|\brais',sn))
        if not ok: return dict(base,kind='verify',label='Large change, being checked')
    verb='Raised' if p>0 else 'Cut'
    if gap: label=f"{verb} {abs(p):.1f}% (from {money(b['amount'],b['currency'])}) sometime between {dh(b['record'])} and {dh(a['record'])} record dates; a declaration in between is missing from our data"
    else: label=f"{verb} {abs(p):.1f}% (from {money(b['amount'],b['currency'])}), announced {dh(first)}"
    return dict(base,kind='raise' if p>0 else 'cut',label=label)
def write(path,html):
    p=os.path.join(DIST,path.strip('/'),'index.html') if not path.endswith('.html') else os.path.join(DIST,path.strip('/'))
    os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(html)
def main():
    data=json.load(open(os.path.join(ROOT,'data','parsed.json')))
    if os.path.exists(DIST): shutil.rmtree(DIST)
    os.makedirs(DIST)
    for f in os.listdir(os.path.join(ROOT,'site','static')): shutil.copy(os.path.join(ROOT,'site','static',f),DIST)
    common=dict(beacon_token=BEACON_TOKEN,referrals=REFERRALS,site_url=SITE_URL,build_id=TODAY.strftime('%Y%m%d'),build_date_human=dh(TODAY))
    urls=[]; companies=[]; upcoming=[]; changes=[]; recent=[]
    for t,c in sorted(data.items(),key=lambda kv:kv[1]['name'].lower()):
        regs=c['regular']
        if not regs: continue
        s=slug(t); L=regs[0]; fq=freq(c); ch=change(regs,fq)
        Lh=dict(amount_h=money(L['amount'],L['currency']),currency=L['currency'],currency_note=CUR_NOTE.get(L.get('currency_basis')) if L['currency'] else None,unit=unit_of(L['snippet']),ex_h=dh(L['record']),record_h=dh(L['record']),pay_h=dh(L['pay']),
                freq=fq,change=ch,filed_h=dh(L['file_date']),form=L['form'],source=L['source'])
        hist=[dict(record_h=dh(r['record']),pay_h=dh(r['pay']),amount_h=money(r['amount'],r['currency']),type='Regular',source=r['source'],rec=r['record']) for r in regs]
        hist+=[dict(record_h=dh(r['record']),pay_h=dh(r['pay']),amount_h=money(r['amount'],r['currency']),type='Special',source=r['source'],rec=r['record']) for r in c['special']]
        hist.sort(key=lambda h:h['rec'],reverse=True)
        drip=None
        for r in regs:
            if r.get('drip_kw'):
                drip=dict(text=("The company's filing mentions a dividend reinvestment plan"+(f" with a {r['drip_disc']}% discount" if r.get('drip_disc') else "")+f" (filing dated {dh(r['file_date'])})."),source=r['source']); break
        name=c['name']
        title=f"{name} ({t}) dividend: ex-date, history, DRIP | MapleDividends"
        desc=f"{name} (TSX: {t}) latest dividend {Lh['amount_h']}, ex-date {Lh['ex_h']}, paid {Lh['pay_h']}. {fq} payer. Dividend history, raises/cuts and DRIP info, with links to the source filings."
        write(f"/dividends/{s}/",env.get_template('company.html').render(title=title,description=desc,path=f"/dividends/{s}/",c=c,L=Lh,history=hist,drip=drip,start_h=dh(START),**common))
        urls.append((f"/dividends/{s}/",L['file_date']))
        companies.append(dict(slug=s,ticker=t,name=name,amount_h=Lh['amount_h'],freq=fq,ex_h=Lh['ex_h']))
        for r in regs+c['special']:
            if TODAY-datetime.timedelta(days=30)<=D(r['record'])<TODAY: recent.append(dict(slug=s,ticker=t,name=name,ex=r['record'],ex_h=dh(r['record']),pay_h=dh(r['pay']),amount_h=money(r['amount'],r['currency'])+(' (special)' if r in c['special'] else ''),freq=fq))
            if D(r['record'])>=TODAY: upcoming.append(dict(slug=s,ticker=t,name=name,ex=r['record'],ex_h=dh(r['record']),pay_h=dh(r['pay']),amount_h=money(r['amount'],r['currency'])+(' (special)' if r in c['special'] else ''),freq=fq))
        # dated by the filing that FIRST announced the new rate; changes whose timing we can't pin down (missing declaration) are left off
        if ch['kind'] in ('raise','cut') and not ch['gap'] and D(ch['first_filed'])>=TODAY-datetime.timedelta(weeks=12):
            fd=D(ch['first_filed']); wk=fd-datetime.timedelta(days=fd.weekday()); a,b=ch['decl'],ch['prev']
            changes.append(dict(slug=s,ticker=t,name=name,kind=ch['kind'],kind_h='Deadly 💀' if ch['kind']=='raise' else 'Not Deadly 👎',pct_h=f"{ch['pct']:+.1f}%",prev_h=money(b['amount'],b['currency']),amount_h=money(a['amount'],a['currency']),ex_h=dh(a['record']),week=wk,filed=ch['first_filed']))
    upcoming.sort(key=lambda e:(e['ex'],e['name'])); changes.sort(key=lambda c:c['filed'],reverse=True)
    recent.sort(key=lambda e:(e['ex'],e['name']),reverse=True)
    rgroups=[dict(date_h=dh(k),rows=list(v)) for k,v in __import__('itertools').groupby(recent,key=lambda e:e['ex'])]
    groups=[dict(date_h=dh(k),rows=list(v)) for k,v in __import__('itertools').groupby(upcoming,key=lambda e:e['ex'])]
    weeks=[dict(week_h=dh(k),rows=list(v)) for k,v in __import__('itertools').groupby(changes,key=lambda c:c['week'])]
    write('/',env.get_template('index.html').render(title="MapleDividends: Canadian dividend calendar, raises & cuts, DRIP info",description="Upcoming TSX ex-dividend dates, dividend raises and cuts, and DRIP info for Canadian dividend stocks, checked against company filings.",path='/',upcoming=upcoming,changes=changes,n_companies=len(companies),**common))
    write('/calendar/',env.get_template('calendar.html').render(title="TSX ex-dividend calendar: upcoming Canadian ex-dates | MapleDividends",description="Upcoming ex-dividend dates for TSX-listed Canadian dividend stocks, with amounts and pay dates, checked against company filings.",path='/calendar/',groups=groups,rgroups=rgroups,today_h=dh(TODAY),**common))
    write('/raises-and-cuts/',env.get_template('raises.html').render(title="Deadly / Not Deadly: Canadian dividend raises & cuts | MapleDividends",description="Deadly or Not Deadly: weekly list of TSX dividend raises and cuts (increases and decreases), checked against company filings.",path='/raises-and-cuts/',weeks=weeks,**common))
    write('/companies/',env.get_template('companies.html').render(title="TSX dividend stocks: list of Canadian dividend payers | MapleDividends",description="Canadian TSX dividend stocks with verified latest dividend, frequency and ex-date.",path='/companies/',rows=companies,**common))
    for p,(tt,dd,content) in PAGES.items():
        write(p,env.get_template('page.html').render(title=tt+" | MapleDividends",description=dd,path=p,content=content,**common))
    write('/404.html',env.get_template('page.html').render(title="Page not found | MapleDividends",description="Page not found.",path='/404.html',noindex=True,content="<h1>Page not found</h1><p>Try the <a href='/companies/'>company list</a> or the <a href='/calendar/'>ex-dividend calendar</a>.</p>",**common))
    import syrup; us_static,us_urls=syrup.build_us(sys.modules[__name__],common)  # Stars & Syrup (U.S. section)
    static=['/','/calendar/','/raises-and-cuts/','/companies/']+us_static+list(PAGES); urls+=us_urls
    sm=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm+=[f"<url><loc>{SITE_URL}{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>" for u in static]
    sm+=[f"<url><loc>{SITE_URL}{u}</loc><lastmod>{lm}</lastmod></url>" for u,lm in urls]
    sm.append('</urlset>'); open(os.path.join(DIST,'sitemap.xml'),'w').write('\n'.join(sm))
    open(os.path.join(DIST,'robots.txt'),'w').write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    open(os.path.join(DIST,'_headers'),'w').write("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n/style.css\n  Cache-Control: public, max-age=31536000, immutable\n")
    n=sum(1 for _ in __import__('glob').glob(os.path.join(DIST,'**','*.html'),recursive=True))
    stats=dict(build_date=TODAY.isoformat(),html_pages=n,company_pages=len(companies),upcoming_exdates=len(upcoming),raises_cuts_12w=len(changes))
    json.dump(stats,open(os.path.join(ROOT,'data','build_stats.json'),'w'),indent=1); print(stats)
CONTACT="hello@mapledividends.com"
PAGES={
 '/about/':("About MapleDividends","About MapleDividends, a free Canadian dividend tracker.",f"""<h1>About MapleDividends</h1>
<p>MapleDividends is a free tracker of dividends paid by TSX-listed Canadian companies: upcoming ex-dividend dates, pay dates, raises, cuts and DRIP details.</p>
<p>It's built and run in Vancouver, B.C. We care about accuracy more than coverage. Every dividend we show links to the company filing it came from, and we leave out anything we couldn't check.</p>
<p>Coverage is limited for now. We start with TSX companies that also file with the U.S. SEC, then add others as we find reliable sources we're allowed to use. See <a href="/methodology/">how we get the data</a>.</p>
<p>Spotted an error? Email <a href="mailto:{CONTACT}">{CONTACT}</a> and include the company and a link to its announcement.</p>{'''
<p>The site is free. Some pages include broker referral links, and we may earn a bonus if you open an account through one. That never affects the data. See our <a href="/affiliate-disclosure/">affiliate disclosure</a>.</p>''' if REFERRALS else ''}"""),
 '/methodology/':("How we get the data","Where MapleDividends dividend data comes from and how it's checked.","""<h1>How we get the data</h1>
<ol><li><strong>Source.</strong> We read company filings (press-release exhibits on forms 6-K and 8-K) published on the U.S. SEC's public EDGAR system. Many TSX companies also list in the U.S. and file their dividend announcements there.</li>
<li><strong>Parsing.</strong> Our software pulls out the dividend amount, record date and pay date as the company wrote them. We don't estimate or forecast dividends.</li>
<li><strong>Checks.</strong> We only publish a declaration when the amount is in a sensible range, the record date is close to the filing date, and the pay date falls on or after the record date (within 120 days). Declarations about preferred shares, debentures and similar securities are excluded. If a filing lists several amounts for the same date (for example, different share classes), we leave them out until a person checks them.</li>
<li><strong>Ex-dates.</strong> Since Canada moved to T+1 settlement on May 27, 2024, the ex-dividend date for regular cash dividends is generally the same as the record date. Special or very large dividends can be different.</li>
<li><strong>Currency.</strong> Many Canadian companies pay dividends in U.S. dollars. We show US$ or C$ when the filing says which (next to the amount, or in a general statement such as "all amounts are in U.S. dollars"), or when we've confirmed it by hand for that company. If we can't tell, we show a plain $ amount exactly as written.</li>
<li><strong>DRIP.</strong> We only show DRIP details the company itself states in a filing. Otherwise the page says "check plan".</li></ol>
<p>Limits: the history only goes back to the filings we've processed (since July 2025), and companies that don't file with the SEC aren't covered yet.</p>"""),
 '/disclaimer/':("Disclaimer: not financial advice","MapleDividends disclaimer.",f"""<h1>Disclaimer</h1>
<p><strong>Not financial advice.</strong> Everything on MapleDividends is general information for educational purposes. It isn't investment, tax or legal advice, and it isn't a recommendation to buy or sell any security. We're not a registered dealer or adviser.</p>
<p>Our data comes from public company filings and is processed automatically. It may contain errors, leave things out, or be out of date. Companies can change or cancel dividends at any time. Before you make any decision, check the company's own announcement, your broker, and if needed a qualified professional.</p>
<p>We aren't liable for any loss that comes from using this site. Past dividends don't guarantee future dividends.</p>
<p>Questions or corrections: <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>"""),
 '/privacy/':("Privacy policy","MapleDividends privacy policy.",f"""<h1>Privacy policy</h1>
<p>Last updated: {dh(TODAY)}.</p>
<p><strong>What we collect.</strong> This site has no accounts, no advertising trackers and no analytics cookies. Our host (Cloudflare) may process standard technical data such as IP addresses to deliver and protect the site. See Cloudflare's privacy policy.</p>{'''
<p><strong>Visitor statistics.</strong> We use Cloudflare Web Analytics to count page views. It doesn't use cookies or local storage and doesn't track you across sites.</p>''' if BEACON_TOKEN else ''}
<p><strong>Market ticker (TradingView).</strong> The price strip at the top of each page is a free third-party widget from TradingView. It loads in a frame from TradingView's servers (tradingview.com and tradingview-widget.com), so your browser sends them standard technical data such as your IP address, browser type and the page you're on. TradingView may use cookies or local storage under its own privacy policy (tradingview.com/privacy-policy/). Prices in the strip are delayed and come from TradingView, not from company filings.</p>
<p><strong>Newsletter.</strong> If you sign up for our email newsletter, we'll collect your email address to send it. It is stored with our email provider, Kit (kit.com). You can unsubscribe at any time using the link in every email. We don't sell your information.</p>
{'''<p><strong>Referral and affiliate links.</strong> Some pages include broker referral links (see our <a href="/affiliate-disclosure/">affiliate disclosure</a>). We don't share any of your information with the broker. If you click one, the broker may use cookies or a referral code to credit the referral, under its own privacy policy.</p>''' if REFERRALS else '''<p><strong>Affiliate links.</strong> If you click an affiliate link (see our <a href="/affiliate-disclosure/">affiliate disclosure</a>), the partner may use cookies to credit the referral.</p>'''}
<p><strong>Contact.</strong> For privacy questions or requests to access or delete your information, email <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>"""),
 '/affiliate-disclosure/':("Affiliate disclosure","How MapleDividends makes money.",f"""<h1>Affiliate disclosure</h1>
<p>MapleDividends is free to use. To pay for it, we may include affiliate or referral links to Canadian financial services, such as online brokerages. If you open an account through one of these links, we may get paid a fee by that company, at no cost to you.</p>
<p>Affiliate relationships never change the dividend data we publish, which comes only from company filings. We'll label affiliate links clearly where they appear.</p>
{('<p>Current referral links: ' + ', '.join(r['name'] for r in REFERRALS) + '. These are personal referral links: if you open and fund an account through one, the broker may give us a bonus (and often gives you one too, under its own terms). They appear in the "Start investing" box, which is labelled as referral links. This isn\'t advice to open any account.</p>') if REFERRALS else '<p>As of today, this site has no affiliate links.</p>'}"""),
}
if __name__=='__main__': main()
