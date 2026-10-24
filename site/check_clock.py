"""Self-check for the exchange-clock session cutoff and the morning/evening refresh line.
Run: python3 site/check_clock.py
Live Yahoo calls run unless CHECK_CLOCK_OFFLINE=1. They print symbol, session date and percent only.
"""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zoneinfo import ZoneInfo
import movers, build
PT, ET, TOR = ZoneInfo('America/Vancouver'), ZoneInfo('America/New_York'), ZoneInfo('America/Toronto')
def expect(cond, msg):
    if not cond: raise SystemExit('FAIL: '+msg)
def test_done():
    fri=datetime.date(2026,10,23); mon=datetime.date(2026,10,26)
    at=lambda h,m: datetime.datetime(2026,10,26,h,m,tzinfo=ET)
    expect(movers._done(fri, at(7,17)), 'prior session kept before the close')
    expect(not movers._done(mon, at(15,59)), 'same-day bar excluded before 16:00')
    expect(movers._done(mon, at(16,0)), 'same-day bar kept at 16:00')
    expect(movers._done(mon, at(19,17)), 'same-day bar kept after the close')
    expect(not movers._done(datetime.date(2026,10,27), at(18,0)), 'future bar excluded')
def test_clock():
    # Friday 4:17pm PT is 7:17pm in Toronto and New York: today's session is done.
    eve=datetime.datetime(2026,10,23,16,17,tzinfo=PT)
    tsx=movers._clock('RY.TO', {}, eve)
    us=movers._clock('AAPL', {'exchangeTimezoneName':'America/New_York'}, eve)
    expect(tsx.tzinfo==TOR and (tsx.hour,tsx.minute)==(19,17), 'TSX fallback is America/Toronto')
    expect(us.tzinfo==ET and (us.hour,us.minute)==(19,17), 'payload zone America/New_York is used')
    expect(movers._done(datetime.date(2026,10,23), tsx) and movers._done(datetime.date(2026,10,23), us), 'evening PT build keeps the same-day close')
    # Monday 4:17am PT is 7:17am Eastern: today's bar is not a completed session.
    morn=datetime.datetime(2026,10,26,4,17,tzinfo=PT)
    early=movers._clock('ENB.TO', {'exchangeTimezoneName':'America/Toronto'}, morn)
    expect((early.hour,early.minute)==(7,17), 'morning PT build is still pre-close in Toronto')
    expect(not movers._done(datetime.date(2026,10,26), early), 'same-day bar stays out before 16:00 Toronto')
    expect(movers._done(datetime.date(2026,10,23), early), 'previous session stays in')
    # A bad payload zone falls back from the symbol, and a naive clock is read in that zone.
    bad=movers._clock('ENB.TO', {'exchangeTimezoneName':'Not/AZone'}, datetime.datetime(2026,10,23,16,0))
    expect(bad.tzinfo==TOR and (bad.hour,bad.minute)==(16,0), 'invalid payload zone falls back to Toronto')
    bare=movers._clock('MSFT', {}, datetime.datetime(2026,10,23,15,59))
    expect(bare.tzinfo==ET and not movers._done(datetime.date(2026,10,23), bare), 'US fallback is New York; 15:59 excludes today')
def test_phrase():
    def pt(y,mo,d,h,m): return datetime.datetime(y,mo,d,h,m,tzinfo=PT)
    expect(build.fresh_when(pt(2026,10,26,4,17))=='before the opening bell', 'Monday 4:17am PT')
    expect(build.fresh_when(pt(2026,10,26,6,29))=='before the opening bell', 'Monday 6:29am PT')
    expect(build.fresh_when(datetime.datetime(2026,10,26,6,29))=='before the opening bell', 'naive clock is Pacific')
    expect(build.fresh_when(pt(2026,10,26,6,30))=='after the close', 'Monday 6:30am PT is not before the bell')
    expect(build.fresh_when(pt(2026,10,23,16,17))=='after the close', 'Friday evening PT')
    expect(build.fresh_when(pt(2026,10,24,5,0))=='after the close', 'Saturday before 6:30am is not a weekday bell')
    expect(build.fresh_when(pt(2026,10,25,8,55))=='after the close', 'Sunday morning')
    expect(build.fresh_when(datetime.datetime(2026,10,26,7,0,tzinfo=ET))=='before the opening bell', '7:00am ET is 4:00am PT')
    expect(build.fresh_when(datetime.datetime(2026,10,26,9,30,tzinfo=ET))=='after the close', '9:30am ET is 6:30am PT')
def test_live():
    if os.environ.get('CHECK_CLOCK_OFFLINE')=='1':
        print('live: skipped'); return
    # power.py calls movers._one(ysym(...), B.TODAY). A 1999 build date must not wipe the quote.
    for t,mkt in (('ENB','TSX'),('MSFT','US')):
        sym=movers.ysym(t,mkt)
        q=movers._one(sym, datetime.date(1999,1,1))
        expect(q and q.get('date') and q.get('close') and 'pct' in q, sym+' returned no completed session')
        now=movers._clock(sym, {'exchangeTimezoneName':'America/Toronto' if mkt=='TSX' else 'America/New_York'})
        expect(q['date']<=now.date().isoformat(), sym+' date is after the exchange date')
        if (now.hour,now.minute)<(16,0): expect(q['date']<now.date().isoformat(), sym+' kept a same-day bar before 16:00')
        print(f"live: {sym} session {q['date']} {q['pct']:+}%")
def main():
    test_done(); test_clock(); test_phrase(); test_live()
    print('ok')
if __name__=='__main__': main()
