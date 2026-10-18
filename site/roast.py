"""Daily Roast 🍁 / Syrup Bath 🥞 blurbs for Leaky Maple vs Golden Pour, plus the Joke of the Day 🥞.
Template-only: every number comes from the verified raise/cut row (name, ticker, % change, old and new amounts with
currency, first-filed date). Templates poke fun at the number and the dividend only: never people, management, fraud,
solvency or predictions. Picked by build date (the build runs in America/Vancouver time, 4:17am PT, before the open),
so the static site changes once a day without any JavaScript."""
import json, os, re, zlib
MINUS='\u2212'
ROAST=[  # worst cut ({pct} is like −55.2%, {pa} like 55.2%)
 "{n} took a chainsaw to its dividend: {old} → {new} ({pct}). The bucket's catching drips, eh.",
 "Somebody left the tap open at {n}: the dividend leaked from {old} to {new} ({pct}). Grab a bigger bucket.",
 "{n} boiled its dividend way down: {old} → {new} ({pct}). Boiling usually makes syrup sweeter. Not this batch.",
 "Sap report for {n} ({t}): {old} went in, {new} comes out. That's a {pa} cut, first filed {date}. Even the squirrels are double-checking the math.",
 "{n}'s dividend went on a strict syrup diet: {old} → {new} ({pct}). Those pancakes are looking a little dry.",
 "The {n} bucket used to fill with {old} a payout. Now it's {new} ({pct}). Drip… drip… drip.",
 "Fresh from the sugar shack: {n} shrank its payout from {old} to {new} ({pct}). Somebody check that spout for holes.",
 "{n} trimmed its dividend like a lumberjack on a deadline: {old} → {new}, a {pa} chop filed {date}.",
]
PRAISE=[  # biggest raise
 "{n} just jumped in a hot syrup bath: {pct} to {new}. Pass the pancakes.",
 "Pour it on! {n} raised its dividend from {old} to {new} ({pct}), first filed {date}. Extra butter for this stack.",
 "{n} ({t}) is soaking in a warm maple bubble bath: dividend up {pa}, {old} → {new}. Rubber duck sold separately.",
 "Sweet news from the sugar shack: {n} bumped its payout to {new} from {old} ({pct}). Grade A amber.",
 "{n}'s dividend went back for seconds: {old} → {new} ({pct}). Stack 'em high.",
 "Hold the napkins: {n} let the syrup flow, raising its dividend {pa} to {new}.",
 "{n} poured a little extra on everyone's plate: {old} → {new} ({pct}). Golden.",
 "Somebody tapped the good tree. {n} raised its dividend {pa}, from {old} to {new}, first filed {date}.",
]
ROAST_SHORT=["{s} cut its dividend {pa} ({old} → {new}). Drip, drip.",
 "{s} boiled its payout down to {new} ({pct}). Bucket's leaking.",
 "{s} took a chainsaw to the dividend: {pct}.",
 "{s}'s dividend went on a syrup diet: {old} → {new}."]
PRAISE_SHORT=["{s} raised its dividend {pa} to {new}. Pass the pancakes.",
 "{s} is in a hot syrup bath: {old} → {new} ({pct}).",
 "{s} let the syrup flow: dividend up {pa}.",
 "{s} went back for seconds: {pct} to {new}."]
DRY=["Not one dividend cut in our {mkt} data. The bucket is bone dry, the tree is fine, and the squirrels are bored. 🎉",
 "Nothing to roast today: zero {mkt} dividend cuts in our data. The sap bucket is collecting dust instead of drips.",
 "The roast is cancelled. No {mkt} dividend cuts in our data, so the bucket is dry and the chainsaw stays in the shed."]
DRY_SHORT=["No cuts to roast. Bucket's dry! 🎉","Zero cuts. The chainsaw stays in the shed."]
EMPTY=["No dividend raises in our {mkt} data yet. The pancakes are stacked and waiting. Plates out."]
EMPTY_SHORT=["No raises yet. Pancakes waiting."]
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
