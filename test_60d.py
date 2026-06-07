import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest import run_backtest, calc_metrics, fetch_ohlcv
from collections import Counter

days = 60

print(f"\n{'='*70}")
print(f"  BACKTEST - SÓ PATTERNS | R:R 1:3 | {days} dias")
print(f"  30m e 1h")
print(f"{'='*70}")

for sym in ['BTC/USDT', 'ETH/USDT']:
    for tf in ['30m', '1h']:
        df = fetch_ohlcv(sym, tf, days=days)
        
        trades = run_backtest(df, 'patterns')
        if not trades:
            print(f"\n  {sym} {tf}: 0 trades")
            continue
        
        m = calc_metrics(trades)
        c = Counter(t['pt'] for t in trades)
        per_day = m['t'] / days
        
        print(f"\n  {sym} {tf}: {m['t']} trades ({per_day:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        for k, v in c.most_common(15):
            wr_info = m['by_type'].get(k, {})
            print(f"    {k:20s}: {v:4d} trades | WR: {wr_info.get('wr', 0):.1f}% | PnL: {wr_info.get('pnl', 0):+.2f}%")
