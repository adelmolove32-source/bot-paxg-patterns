import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest import run_backtest, calc_metrics, fetch_ohlcv
from collections import Counter

for sym in ['BTC/USDT', 'ETH/USDT']:
    for tf in ['3m', '5m', '15m']:
        df = fetch_ohlcv(sym, tf, days=30)
        
        for strat in ['patterns', 'all']:
            trades = run_backtest(df, strat)
            if not trades:
                print(f"  {sym} {tf} {strat}: 0 trades")
                continue
            m = calc_metrics(trades)
            c = Counter(t['pt'] for t in trades)
            per_day = m['t'] / 30
            print(f"\n  {sym} {tf} {strat}: {m['t']} trades ({per_day:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f}")
            for k, v in c.most_common(5):
                print(f"    {k}: {v}")
