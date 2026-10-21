"""Daily Roast 🍁 / Syrup Bath 🥞 blurbs for Leaky Maple vs Golden Pour, plus the Joke of the Day 🥞.
Template-only: every number comes from the daily price row (name, ticker, % change, prior and last close with
currency, session date). Templates poke fun at the number and the share price only: never people, management, fraud,
solvency or predictions. Picked by build date (the build runs early morning America/Vancouver time, before the open),
so the static site changes once a day without any JavaScript."""
import json, os, re, zlib
MINUS='\u2212'
ROAST=[  # biggest % price loser at the last close ({old}=prior close, {new}=last close, {date}=session date)
 "{n} sprang a leak: {old} → {new} at the {date} close ({pct}). The bucket's catching drips, eh.",
 "Somebody left the tap open at {n}: the shares dripped from {old} to {new} ({pct}) on {date}. Grab a bigger bucket.",
 "{n} ({t}) boiled down to {new} at the {date} close, from {old}. That's {pct}. Not the sweet kind of boiling.",
 "Sap report for {n} ({t}): {pa} lower on {date}, {old} → {new}. Worst drip in our list.",
 "{n}'s share price went on a syrup diet: {old} → {new} ({pct}) on {date}.",
 "Drip… drip… {n} closed {date} at {new}, down {pa} from {old}.",
 "Fresh from the sugar shack: {n} slid {pa} on {date}, {old} → {new}. Check that spout for holes.",
 "{n} got the chainsaw on {date}: {old} → {new}, a {pa} chop. Biggest drop in our list.",
]
PRAISE=[  # biggest % price gainer at the last close
 "{n} hopped in a hot syrup bath: {pct} to {new} at the {date} close. Pass the pancakes.",
 "Pour it on! {n} climbed from {old} to {new} ({pct}) on {date}. Extra butter for this stack.",
 "{n} ({t}) is soaking in a warm maple bubble bath: up {pa} on {date}, {old} → {new}. Rubber duck sold separately.",
 "Sweet news from the sugar shack: {n} closed {date} at {new}, up from {old} ({pct}). Grade A amber.",
 "{n}'s shares went back for seconds on {date}: {old} → {new} ({pct}). Stack 'em high.",
 "Hold the napkins: {n} let the syrup flow, up {pa} to {new} at the {date} close.",
 "{n} poured a little extra on the plate: {old} → {new} ({pct}) on {date}. Golden.",
 "Somebody tapped the good tree. {n} gained {pa} on {date}, from {old} to {new}. Top of our list.",
]
ROAST_SHORT=["{s} dripped {pa} ({old} → {new}). Drip, drip.",
 "{s} boiled down to {new} ({pct}). Bucket's leaking.",
 "{s} got the chainsaw: {pct} at the close.",
 "{s} went on a syrup diet: {old} → {new}."]
PRAISE_SHORT=["{s} rose {pa} to {new}. Pass the pancakes.",
 "{s} is in a hot syrup bath: {old} → {new} ({pct}).",
 "{s} let the syrup flow: up {pa}.",
 "{s} went back for seconds: {pct} to {new}."]
DRY=["Not one {mkt} stock in our list closed lower. The bucket is bone dry and the squirrels are bored. 🎉",
 "Nothing to roast: no {mkt} losers in our list at the last close. The sap bucket is collecting dust instead of drips.",
 "The roast is cancelled. Nothing in our {mkt} list fell at the last close, so the chainsaw stays in the shed."]
DRY_SHORT=["No losers to roast. Bucket's dry! 🎉","Nothing fell. The chainsaw stays in the shed."]
EMPTY=["No {mkt} gainers in our list at the last close (or prices weren't available). The pancakes are waiting."]
EMPTY_SHORT=["No gainers. Pancakes waiting."]
SUFFIX=re.compile(r'(,?\s+(Inc|Inc\.|Incorporated|Corp\.?|Corporation|Company|Co\.|Ltd\.?|Limited|plc|N\.V\.|S\.A\.|& Co\.?))+$',re.I)
def short_name(n):
    n=re.sub(r'^The\s+|\s*\(The\)$','',n.strip()); m=SUFFIX.sub('',n).strip(' ,')
    return m or n
def _pct(p): return (MINUS if p<0 else '+')+f"{abs(p):.1f}%"
def _pick(lst,today,salt,off=0):
    """Rotate by date: consecutive days get different variants; the salt keeps the sides out of lockstep."""
    return lst[(today.toordinal()+zlib.crc32(salt.encode())+off)%len(lst)]
def _fill(tpl,p):
    n=short_name(p['name'])
    return tpl.format(n=n,s=n if len(n)<=16 else p['ticker'],t=p['ticker'],old=p['prev_h'],new=p['amount_h'],pct=_pct(p['pct']),pa=f"{abs(p['pct']):.1f}%",date=p['filed_h'])
def blurbs(d,today,mkt):
    """d = leaky.side() result. Returns dict(roast, praise, roast_short, praise_short)."""
    c,r=d.get('cut'),d.get('raise_'); out={}; o=0 if mkt=='TSX' else 3  # keep the two tabs on different variants
    if c: out['roast']=_fill(_pick(ROAST,today,'roast',o),c); out['roast_short']=_fill(_pick(ROAST_SHORT,today,'rs',o),c)
    else: out['roast']=_pick(DRY,today,'dry',o).format(mkt=mkt); out['roast_short']=_pick(DRY_SHORT,today,'ds',o)
    if r: out['praise']=_fill(_pick(PRAISE,today,'praise',o),r); out['praise_short']=_fill(_pick(PRAISE_SHORT,today,'ps',o),r)
    else: out['praise']=_pick(EMPTY,today,'em'+mkt).format(mkt=mkt); out['praise_short']=EMPTY_SHORT[0]
    return out
def joke(root,today):
    """Joke of the Day: walks through data/jokes.json one per day (no repeats until the list runs out)."""
    p=os.path.join(root,'data','jokes.json')
    try: js=[j for j in json.load(open(p))['jokes'] if j.strip()]
    except (OSError,ValueError,KeyError): return None
    if not js: return None
    i=today.toordinal()%len(js); return dict(text=js[i],n=i+1,of=len(js))
