"""Stars & Syrup: U.S. dividend stocks popular with Canadians. data/us_parsed.json -> /stars-and-syrup/ and /us/<ticker>/.
Uses the helpers in build.py (passed in as B) so the U.S. pages follow the same rules as the TSX pages."""
import json, os, datetime
SECTION='/stars-and-syrup/'
US_CUR_NOTE="U.S.-listed company; amounts are in U.S. dollars"
def build_us(B,common):
    """Writes the section; returns (static_paths, [(path, lastmod)]) for the sitemap. No data file = no section."""
    p=os.path.join(B.ROOT,'data','us_parsed.json')
    if not os.path.exists(p): return [],[]
    data=json.load(open(p)); uni={u['ticker']:u for u in json.load(open(os.path.join(B.ROOT,'data','us_universe.json')))}
    D,dh,money,TODAY=B.D,B.dh,B.money,B.TODAY
    mp=os.path.join(B.ROOT,'data','us_ir_manual.json')
    manual={k:v for k,v in (json.load(open(mp)).items() if os.path.exists(mp) else []) if not k.startswith('_')}
    rows=[]; upcoming=[]; changes=[]; urls=[]; gaps=[]
    for t in sorted(uni,key=lambda t:uni[t]['name'].lower().removeprefix('the ')):
        c=data.get(t) or dict(ticker=t,name=uni[t]['name'],regular=[],special=[],ambiguous=[])
        regs=list(c['regular'])
        for m in manual.get(t,[]):  # person-checked IR announcements not yet in EDGAR; never override an EDGAR declaration
            if not any(r['record']==m['record'] for r in regs):
                regs.append(dict(amount=m['amount'],currency='USD',currency_basis='us',record=m['record'],pay=m['pay'],file_date=m.get('announced') or m['record'],first_filed=m.get('announced') or m['record'],
                                 form='IR',source=m['source'],snippet=m.get('quote',''),frequency_kw=m.get('frequency'),increase_kw=False,decrease_kw=False))
        regs.sort(key=lambda r:(r['record'],r['file_date']),reverse=True); c=dict(c,regular=regs)
        if not regs: gaps.append(dict(ticker=t,name=uni[t]['name'])); continue
        for r in regs+c['special']:
            if not r.get('currency'): r['currency'],r['currency_basis']='USD','us'  # U.S. issuers state plain "$"
        ex=uni[t].get('exchange') or 'NYSE'
        s=B.slug(t); L=regs[0]; fq=B.freq(c)
        if fq=='Not stated' and len(regs)>=3:  # U.S. quarterly payers often space record dates 75-105 days apart
            g=sorted((D(a['record'])-D(b['record'])).days for a,b in zip(regs,regs[1:]))[(len(regs)-1)//2]
            if 60<=g<=120: fq='Quarterly'
        ch=B.change(regs,fq)
        if ch.get('label'): ch['label']=ch['label'].replace(', announced ',', first reported ')
        if ch['kind'] in ('raise','cut'): ch=dict(ch,label=('Deadly 💀 ' if ch['kind']=='raise' else 'Not Deadly 👎 ')+ch['label'])
        note=US_CUR_NOTE if L.get('currency_basis')=='us' else B.CUR_NOTE.get(L.get('currency_basis'))
        src_label='Company announcement (investor relations page)' if L['form']=='IR' else None
        Lh=dict(source_label=src_label,amount_h=money(L['amount'],L['currency']),currency=L['currency'],currency_note=note,unit=B.unit_of(L['snippet']),ex_h=dh(L['record']),record_h=dh(L['record']),pay_h=dh(L['pay']),
                freq=fq,change=ch,filed_h=dh(L['file_date']),form=L['form'],source=L['source'])
        hist=[dict(record_h=dh(r['record']),pay_h=dh(r['pay']),amount_h=money(r['amount'],r['currency']),type='Regular',source=r['source'],rec=r['record'],src='IR page' if r['form']=='IR' else None) for r in regs]
        hist+=[dict(record_h=dh(r['record']),pay_h=dh(r['pay']),amount_h=money(r['amount'],r['currency']),type='Special',source=r['source'],rec=r['record']) for r in c['special']]
        hist.sort(key=lambda h:h['rec'],reverse=True)
        gap=B.GAP.get(fq,91)
        stale=(TODAY-D(L['record'])).days>gap+45
        lag=L['form'] in ('10-Q','10-K')
        stale_note=None if not (stale or lag) else (f"Heads up: the latest declaration we could verify has a record date of {dh(L['record'])}. {c['name']} has probably declared newer dividends that aren't in the SEC filings we read yet, so check the company's investor relations site for the current one.") if stale else (
            f"{c['name']} doesn't file each dividend announcement with the SEC, so this comes from its quarterly or annual report. A newer declaration may be out that we haven't picked up yet; check the company's investor relations site.")
        name=c['name']; path=f"/us/{s}/"
        title=f"{name} ({t}) dividend: ex-date, history, raises & cuts | Stars & Syrup | MapleDividends"
        desc=f"{name} ({ex}: {t}) latest dividend {Lh['amount_h']}, ex-date {Lh['ex_h']}, paid {Lh['pay_h']}. U.S. dividend history, raises and cuts for Canadian investors, with links to the SEC filings."
        B.write(path,B.env.get_template('company.html').render(title=title,description=desc,path=path,c=c,L=Lh,history=hist,drip=None,start_h=dh(B.START),
                exchange=ex,list_url=SECTION,list_name='Stars & Syrup 🇺🇸',us=True,stale_note=stale_note,**common))
        urls.append((path,L['file_date']))
        rows.append(dict(slug=s,ticker=t,name=name,exchange=ex,amount_h=Lh['amount_h'],freq=fq,ex_h=Lh['ex_h'],ch=ch,stale=stale,lag=lag))
        for r in regs+c['special']:
            if D(r['record'])>=TODAY: upcoming.append(dict(slug=s,ticker=t,name=name,ex=r['record'],ex_h=dh(r['record']),pay_h=dh(r['pay']),amount_h=money(r['amount'],r['currency'])+(' (special)' if r in c['special'] else ''),freq=fq))
        if ch['kind'] in ('raise','cut') and not ch['gap']:
            a,b=ch['decl'],ch['prev']
            changes.append(dict(slug=s,ticker=t,name=name,kind=ch['kind'],kind_h='Deadly 💀' if ch['kind']=='raise' else 'Not Deadly 👎',pct_h=f"{ch['pct']:+.1f}%",prev_h=money(b['amount'],b['currency']),amount_h=money(a['amount'],a['currency']),ex_h=dh(a['record']),filed=ch['first_filed'],filed_h=dh(ch['first_filed']),pct=ch['pct']))
    upcoming.sort(key=lambda e:(e['ex'],e['name'])); changes.sort(key=lambda c:c['filed'],reverse=True)
    B.US_CHANGES=changes  # Leaky Maple / Golden Pour U.S. tab
    B.write(SECTION,B.env.get_template('syrup.html').render(
        title="Stars & Syrup: U.S. dividend stocks for Canadians (ex-dates, raises & cuts) | MapleDividends",
        description="U.S. dividend stocks popular with Canadian investors: upcoming ex-dividend dates, latest dividends in US$, raises and cuts, checked against SEC filings.",
        path=SECTION,rows=rows,upcoming=upcoming,changes=changes[:12],gaps=gaps,**common))
    return [SECTION],urls
