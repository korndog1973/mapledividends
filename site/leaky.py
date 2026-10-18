"""Leaky Maple vs Golden Pour: the worst recent dividend cut (syrup leaking from a tapped maple) and the biggest recent
dividend raise (syrup pouring onto pancakes). Built only from the raises/cuts we already verify against company filings,
so there's no new data source, key or licence. The live price movers under the art are TradingView's free embeddable
Stock Market (hotlists) widget, which loads in the visitor's browser straight from TradingView."""
import os, datetime
PATH='/leaky-maple/'
OG='og.png'
WEEKS=12  # same window as the raises & cuts page
MINUS='\u2212'
def pct_h(p): return (MINUS if p<0 else '+')+f"{abs(p):.1f}%"
def _pick(chg,kind,today):
    xs=[c for c in chg if c['kind']==kind]
    if not xs: return None
    win=[c for c in xs if datetime.date.fromisoformat(c['filed'])>=today-datetime.timedelta(weeks=WEEKS)]
    if win:
        best=(min if kind=='cut' else max)(win,key=lambda c:(c['pct'],c['filed']))
        return dict(best,recent=True)
    return dict(max(xs,key=lambda c:c['filed']),recent=False)  # nothing in the window: most recent one, with its date
def side(chg,today):
    """chg: verified raises/cuts (no 'gap' changes) with ticker, name, url, kind, pct, filed (ISO), filed_h."""
    chg=[dict(c,big_h=pct_h(c['pct'])) for c in chg]
    win=[c for c in chg if datetime.date.fromisoformat(c['filed'])>=today-datetime.timedelta(weeks=WEEKS)]
    return dict(cut=_pick(chg,'cut',today),raise_=_pick(chg,'raise',today),
                cuts=sorted([c for c in win if c['kind']=='cut'],key=lambda c:c['pct'])[:5],
                raises=sorted([c for c in win if c['kind']=='raise'],key=lambda c:-c['pct'])[:5])
def og_png(path,ca):
    """1200x630 share card with both tickers. Pillow only (pure pip wheel, no system libraries). Returns False if
    Pillow isn't installed, in which case the page simply has no og:image."""
    try: from PIL import Image, ImageDraw, ImageFont
    except ImportError: return False
    S=2; W,H=1200*S,630*S
    im=Image.new('RGB',(W,H),'#fffaf0'); d=ImageDraw.Draw(im)
    def font(px,bold=True):
        for f in (('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),'/usr/share/fonts/truetype/dejavu/'+('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')):
            try: return ImageFont.truetype(f,px*S)
            except OSError: pass
        return ImageFont.load_default(size=px*S)
    def text(xy,s,px,fill,anchor='mm',bold=True,maxw=None):
        while maxw and px>10 and d.textlength(s,font=font(px,bold))>maxw*S: px-=2
        d.text((xy[0]*S,xy[1]*S),s,font=font(px,bold),fill=fill,anchor=anchor)
    def E(cx,cy,rx,ry,**k): d.ellipse([(cx-rx)*S,(cy-ry)*S,(cx+rx)*S,(cy+ry)*S],**k)
    def P(pts,**k): d.polygon([(x*S,y*S) for x,y in pts],**k)
    d.rectangle([0,0,600*S,H],fill='#fde8dc'); d.rectangle([600*S,0,W,H],fill='#fef3c7')
    cut=ca.get('cut'); r=ca.get('raise_')
    text((300,52),'LEAKY MAPLE',42,'#7f1d1d'); text((300,94),'worst recent dividend cut',24,'#7f1d1d',bold=False)
    text((900,52),'GOLDEN POUR',42,'#78350f'); text((900,94),'biggest recent dividend raise',24,'#78350f',bold=False)
    # --- left: tapped maple + sap bucket
    E(300,600,380,60,fill='#cfe8bd')
    P([(108,580),(122,300),(168,300),(186,580)],fill='#7c4a26')
    for cx,cy,rr,c in [(90,215,58,'#ea580c'),(150,180,70,'#dc2626'),(215,215,60,'#f97316'),(110,265,50,'#f59e0b'),(190,268,52,'#b91c1c'),(55,262,36,'#dc2626')]: E(cx,cy,rr,rr,fill=c)
    d.rounded_rectangle([160*S,372*S,250*S,388*S],radius=5*S,fill='#9ca3af'); P([(244,372),(256,372),(260,398),(248,398)],fill='#9ca3af')
    P([(254,405),(246,420),(254,428),(262,420)],fill='#d97706'); E(254,420,8,8,fill='#d97706')
    P([(205,440),(505,440),(485,568),(225,568)],fill='#d1d5db',outline='#6b7280',width=3*S)
    d.line([(208*S,462*S),(502*S,462*S)],fill='#9ca3af',width=5*S)
    E(355,440,150,12,fill='#78350f')
    text((355,505),cut['ticker'] if cut else '-',76,'#7f1d1d',maxw=230)
    text((355,548),(cut['big_h'] if cut else 'no cuts!'),30,'#dc2626')
    # --- right: pancakes, butter, flag, jug pouring
    E(900,552,240,24,fill='#ffffff',outline='#cbd5e1',width=3*S)
    for k in range(5):
        y=530-k*24; E(900,y,170,26,fill='#b45309'); E(900,y-9,170,26,fill='#f2b45a' if k%2==0 else '#eaa84a')
    E(900,425,150,20,fill='#d97706')
    for x,h in [(795,55),(860,80),(955,45),(1010,65)]: d.rounded_rectangle([(x-9)*S,428*S,(x+9)*S,(428+h)*S],radius=9*S,fill='#d97706')
    P([(870,402),(882,390),(930,390),(918,402)],fill='#fef9c3'); d.rectangle([870*S,402*S,918*S,416*S],fill='#fde047')
    jug=Image.new('RGBA',(120*S,210*S),(0,0,0,0)); jd=ImageDraw.Draw(jug)
    jd.rounded_rectangle([10*S,60*S,110*S,205*S],radius=18*S,fill='#c2690a',outline='#78350f',width=3*S)
    jd.rectangle([42*S,10*S,78*S,64*S],fill='#b45309',outline='#78350f',width=3*S)
    jd.rounded_rectangle([25*S,100*S,95*S,165*S],radius=8*S,fill='#fffbeb')
    jd.rectangle([56*S,0,64*S,8*S],fill=(255,0,255,255))  # marker for the mouth
    jug=jug.rotate(128,expand=True,resample=Image.BICUBIC)
    px=jug.load(); mx=my=n=0
    for yy in range(jug.size[1]):
        for xx in range(jug.size[0]):
            p=px[xx,yy]
            if p[3]>200 and p[0]>200 and p[1]<60 and p[2]>200: mx+=xx; my+=yy; n+=1; px[xx,yy]=(0,0,0,0)
    mx,my=(mx//max(n,1),my//max(n,1))
    ox,oy=1035*S-mx,215*S-my
    d.line([(1035*S,215*S),(985*S,300*S),(955*S,405*S)],fill='#d97706',width=14*S,joint='curve')
    im.paste(jug,(ox,oy),jug)
    d.line([(760*S,440*S),(760*S,200*S)],fill='#c9a46f',width=6*S)
    P([(762,200),(930,200),(905,250),(930,300),(762,300)],fill='#ffffff',outline='#047857',width=4*S)
    text((836,236),r['ticker'] if r else '-',52,'#065f46',maxw=130)
    text((836,280),r['big_h'] if r else '',24,'#047857')
    d.rectangle([0,H-50*S,W,H],fill='#ffffff'); text((600,606),'mapledividends.com/leaky-maple  ·  for fun, not advice',22,'#374151',bold=False)
    im.resize((1200,630),Image.LANCZOS).save(path,optimize=True); return True
def build(B,common,ca_chg,us_chg):
    """Writes /leaky-maple/ (+ og.png); returns (context for the home page teaser, [static paths])."""
    ca=side(ca_chg,B.TODAY); us=side(us_chg,B.TODAY) if us_chg is not None else None
    os.makedirs(os.path.join(B.DIST,PATH.strip('/')),exist_ok=True)
    og=PATH+OG+'?v='+B.TODAY.strftime('%Y%m%d') if og_png(os.path.join(B.DIST,PATH.strip('/'),OG),ca) else None
    c,r=ca['cut'],ca['raise_']
    bits=[f"Leaky Maple: {c['name']} ({c['ticker']}) dividend cut {c['big_h']}" if c else "No recent dividend cuts",
          f"Golden Pour: {r['name']} ({r['ticker']}) dividend raise {r['big_h']}" if r else "no recent dividend raises"]
    B.write(PATH,B.env.get_template('leaky.html').render(
        title="Leaky Maple vs Golden Pour: worst dividend cut vs biggest dividend raise | MapleDividends",
        description=f"{bits[0]}. {bits[1]}. The worst TSX dividend cut and biggest dividend raise of the last {WEEKS} weeks, checked against company filings. For fun, not advice.",
        path=PATH,ca=ca,us=us,weeks=WEEKS,og_image=og,**common))
    return dict(ca=ca),[PATH]
