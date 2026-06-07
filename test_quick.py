import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest import run_backtest, calc_metrics, fetch_ohlcv
from collections import Counter

sym = 'BTC/USDT'
tf = '5m'
days = 14

print(f"\n  Buscando {sym} {tf} ({days} dias)...")
df = fetch_ohlcv(sym, tf, days=days)
print(f"  {len(df)} barras")

for strat in ['elephant', 'wick', 'patterns', 'all']:
    trades = run_backtest(df, strat)
    if not trades:
        print(f"  {strat}: 0 trades")
        continue
    m = calc_metrics(trades)
    c = Counter(t['pt'] for t in trades)
    per_day = m['t'] / days
    print(f"\n  {strat}: {m['t']} trades ({per_day:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f}")
    for k, v in c.most_common(10):
        print(f"    {k}: {v}")
