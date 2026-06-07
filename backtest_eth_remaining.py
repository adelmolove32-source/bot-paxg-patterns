import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(r'C:\Users\muril\Desktop\bot btc4')
from backtest_5td import run_backtest_limited, calc_metrics
from backtest import fetch_ohlcv

for sym, tf in [('ETH/USDT','5m'), ('ETH/USDT','15m')]:
    print(f'{sym} {tf}...', end=' ', flush=True)
    df = fetch_ohlcv(sym, tf, days=60)
    trades = run_backtest_limited(df, 5)
    m = calc_metrics(trades, initial=200)
    per_day = m['t'] / 60
    final_str = f"${m['final']:,.0f}"
    print(f"{m['t']} trades ({per_day:.1f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}% | $200 -> {final_str}")
    for pt, data in sorted(m['by_type'].items(), key=lambda x: x[1]['pnl'], reverse=True):
        if data['n'] >= 3:
            print(f"  {pt:20s}: {data['n']:3d} trades | WR: {data['wr']:5.1f}% | PnL: {data['pnl']:+7.1f}%")
