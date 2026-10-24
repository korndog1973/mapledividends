"""SEO helpers: JSON-LD (Organization/WebSite, BreadcrumbList, Dataset + FAQPage on ticker pages), Open Graph images
(one branded /og.png + one per-ticker card), sector hubs, the /us/ index, internal-link blocks.
Only facts already on the page go into structured data."""
import os, re
from PIL import Image, ImageDraw, ImageFont
FONT_B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def _font(p,n):
    try: return ImageFont.truetype(p,n)
    except OSError: return ImageFont.load_default()
# Hand-classified sector hubs (only tickers we actually have pages for are shown)
SECTORS={
 'banks':dict(name='Canadian bank stocks',short='Banks',tickers=['BMO','BNS','CM','TD','RY','NA','EQB','CWB','LB'],
              intro='Big Canadian banks and their latest declared dividends: ex-dates, pay dates and raises, from their own filings.'),
 'pipelines':dict(name='Canadian pipeline stocks',short='Pipelines',tickers=['ENB','TRP','PPL','SOBO','KEY','GEI'],
              intro='Canadian pipeline and midstream dividend payers: latest declared dividends, ex-dates and pay dates.'),
 'utilities':dict(name='Canadian utility stocks',short='Utilities',tickers=['FTS','EMA','H','AQN','BEP','CU','ACO','CPX','ALA'],
              intro='Canadian utility dividend payers: latest declared dividends, ex-dates and pay dates.'),
 'telecom':dict(name='Canadian telecom stocks',short='Telecom',tickers=['BCE','T','RCI','QBR'],
              intro='Canadian telecom dividend payers: latest declared dividends, ex-dates and pay dates.'),
}
def sector_of(t):
    for k,s in SECTORS.items():
        if t in s['tickers']: return k
    return None
def og_image(out,big,sub,foot):
    W,H=1200,630; im=Image.new('RGB',(W,H),'#fff8f1'); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,18],fill='#b91c1c'); d.rectangle([0,H-90,W,H],fill='#b91c1c')
    d.text((60,56),'MapleDividends',font=_font(FONT_B,54),fill='#b91c1c')
    f=96
    while f>40 and d.textlength(big,font=_font(FONT_B,f))>W-120: f-=4
    d.text((60,190),big,font=_font(FONT_B,f),fill='#1f2937')
    y=200+f+30
    for line in sub[:3]:
        d.text((60,y),line,font=_font(FONT,40),fill='#374151'); y+=58
    d.text((60,H-66),foot,font=_font(FONT_B,34),fill='#ffffff')
    os.makedirs(os.path.dirname(out),exist_ok=True); im.save(out,optimize=True)
def crumbs(path,leaf):
    if path in ('/','/404.html'): return []
    seg=path.strip('/').split('/')
    c=[('Home','/')]
    if seg[0]=='dividends' and len(seg)>1: c.append(('Companies','/companies/'))
    elif seg[0]=='us' and len(seg)>1: c.append(('U.S. dividend stocks','/us/'))
    elif seg[0]=='sectors' and len(seg)>1: c.append(('Sectors','/sectors/'))
    c.append((leaf,path)); return c
def ld_breadcrumbs(site,path,leaf):
    c=crumbs(path,leaf)
    if not c: return None
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":site+u} for i,(n,u) in enumerate(c)]}
def ld_home(site):
    return [{"@context":"https://schema.org","@type":"Organization","name":"MapleDividends","url":site+"/","logo":site+"/og.png",
             "description":"Free Canadian dividend tracker built from company filings.","parentOrganization":{"@type":"Organization","name":"CHASELIST"}},
            {"@context":"https://schema.org","@type":"WebSite","name":"MapleDividends","url":site+"/","inLanguage":"en-CA"}]
def faq(c,L,nxt,dh):
    t=c['ticker']; q=[]
    if nxt: q.append((f"When is the next {t} ex-dividend date?",f"The next {c['name']} ex-dividend date on file is {dh(nxt['record'])}, for a dividend of {nxt['amount_h']} paid {dh(nxt['pay'])}, per the company's filing."))
    else: q.append((f"When is the next {t} ex-dividend date?",f"The latest {c['name']} ex-dividend date in our verified data is {L['ex_h']} (paid {L['pay_h']}). A newer one hasn't shown up in the filings we've checked yet."))
    q.append((f"How much is the latest {t} dividend?",f"{L['amount_h']} per {L['unit']}, with a record date of {L['record_h']} and a pay date of {L['pay_h']}."))
    if L['freq']!='Not stated': q.append((f"How often does {t} pay dividends?",f"{c['name']} pays {L['freq'].lower()} dividends, based on its filings."))
    return q
def ld_company(site,path,c,L,faqs,sources,dmod,market='TSX'):
    out=[{"@context":"https://schema.org","@type":"Dataset","name":f"{c['name']} ({c['ticker']}) dividend history",
          "description":f"Declared dividends for {c['name']} ({market}: {c['ticker']}): amount, record/ex-date and pay date, taken from company filings.",
          "url":site+path,"creator":{"@type":"Organization","name":"MapleDividends","url":site+"/"},"dateModified":dmod,
          "variableMeasured":["Dividend amount","Ex-dividend / record date","Pay date"],"isBasedOn":sources[:10],"isAccessibleForFree":True}]
    if faqs: out.append({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":a,"acceptedAnswer":{"@type":"Answer","text":b}} for a,b in faqs]})
    return out
