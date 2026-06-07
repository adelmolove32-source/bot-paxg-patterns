"""
BACKTEST - MAX 5 TRADES/DIA | 3m, 5m, 15m | 60 dias
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from backtest import fetch_ohlcv, sim_exit, calculate_stop_dist, calculate_target
from config import RR_RATIO, STOP_MODE
from strategy import calculate_indicators
from patterns import detect_all_patterns

MAX_TRADES_PER_DAY = 5
DAYS = 60

def run_backtest_limited(df, max_per_day=5):
    """Backtest com limite de trades por dia"""
    df = calculate_indicators(df)
    n = len(df)
    patterns = detect_all_patterns(df)
    H = df['h'].values
    L = df['l'].values

    trades = []
    daily_count = {}

    for pat in patterns:
        idx = pat['index']
        if idx >= n:
            continue

        trade_date = df.index[idx].date()
        if trade_date not in daily_count:
            daily_count[trade_date] = 0
        if daily_count[trade_date] >= max_per_day:
            continue

        entry_price = pat['entry']
        stop = pat['stop']
        target = pat['target']
        direction = pat['direction']

        exit_price, reason, bars_held = sim_exit(df, idx, stop, target, n, direction)

        if direction == 'buy':
            pnl = ((exit_price - entry_price) / entry_price * 100)
        else:
            pnl = ((entry_price - exit_price) / entry_price * 100)

        trades.append({
            'et': df.index[idx], 'ep': entry_price, 'pnl': pnl,
            'xr': reason, 'bh': bars_held, 'pt': pat['label'],
            'bull': direction == 'buy', 'date': trade_date
        })
        daily_count[trade_date] += 1

    trades.sort(key=lambda x: x['et'])
    return trades

def calc_metrics(trades, initial=200):
    if not trades:
        return None
    d = pd.DataFrame(trades)
    w = d[d['pnl'] > 0]
    l = d[d['pnl'] <= 0]

    eq = initial
    pk = initial
    mdd = 0
    for t in trades:
        eq *= (1 + t['pnl'] / 100)
        if eq > pk:
            pk = eq
        dd = (pk - eq) / pk * 100
        if dd > mdd:
            mdd = dd

    pf = abs(w['pnl'].sum() / l['pnl'].sum()) if len(l) > 0 and l['pnl'].sum() != 0 else 999

    by_type = {}
    for pt in d['pt'].unique():
        sub = d[d['pt'] == pt]
        sw = sub[sub['pnl'] > 0]
        by_type[pt] = {
            'n': len(sub),
            'wr': round(len(sw) / len(sub) * 100, 1) if len(sub) > 0 else 0,
            'pnl': round(sub['pnl'].sum(), 2)
        }

    return {
        't': len(d), 'w': len(w),
        'wr': round(len(w) / len(d) * 100, 1),
        'pnl': round(d['pnl'].sum(), 2),
        'pf': round(min(pf, 999), 2),
        'mdd': round(mdd, 2),
        'final': round(eq, 2),
        'by_type': by_type
    }


print(f"\n{'='*75}")
print(f"  BACKTEST - MAX 5 TRADES/DIA | R:R 1:3 | {DAYS} dias | Banca $200")
print(f"{'='*75}")

combos = [
    ('BTC/USDT', '3m'),
    ('BTC/USDT', '5m'),
    ('BTC/USDT', '15m'),
    ('ETH/USDT', '3m'),
    ('ETH/USDT', '5m'),
    ('ETH/USDT', '15m'),
]
results = []

for sym, tf in combos:
    print(f"\n  {sym} {tf}...", end=" ", flush=True)
    try:
        df = fetch_ohlcv(sym, tf, days=DAYS)
        trades = run_backtest_limited(df, MAX_TRADES_PER_DAY)
        if not trades:
            print("0 trades")
            continue
        m = calc_metrics(trades, initial=200)
        per_day = m['t'] / DAYS
        print(f"{m['t']} trades ({per_day:.1f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}% | $200 -> ${m['final']:,.0f}")
        results.append({
            'par': sym, 'tf': tf, 'trades': m['t'], 'per_day': per_day,
            'wr': m['wr'], 'pnl': m['pnl'], 'pf': m['pf'], 'mdd': m['mdd'],
            'final': m['final'], 'by_type': m['by_type']
        })
    except Exception as e:
        print(f"ERRO: {e}")

# Ranking
print(f"\n{'='*75}")
print(f"  RANKING - MAX 5 TRADES/DIA (ordenado por lucro)")
print(f"{'='*75}")
print(f"\n  {'#':>2} {'Par/TF':<15} {'T':>5} {'T/dia':>6} {'WR%':>6} {'PnL%':>8} {'PF':>5} {'MDD%':>6} {'$200->':>8}")
print(f"  {'-'*70}")

results.sort(key=lambda x: x['pnl'], reverse=True)
for i, r in enumerate(results, 1):
    medal = f"{i}o"
    print(f"  {medal:>2} {r['par']+'/'+r['tf']:<15} {r['trades']:>5} {r['per_day']:>5.1f} {r['wr']:>5.1f}% {r['pnl']:>7.1f}% {r['pf']:>5.2f} {r['mdd']:>5.1f}% ${r['final']:>7,.0f}")

# Detalhes por pattern no top 3
print(f"\n{'='*75}")
print(f"  TOP 3 - DETALHES POR PATTERN")
print(f"{'='*75}")

for r in results[:3]:
    print(f"\n  {r['par']}/{r['tf']} - PnL: {r['pnl']:+.1f}%")
    sorted_pt = sorted(r['by_type'].items(), key=lambda x: x[1]['pnl'], reverse=True)
    for pt, data in sorted_pt:
        if data['n'] >= 3:
            print(f"    {pt:20s}: {data['n']:3d} trades | WR: {data['wr']:5.1f}% | PnL: {data['pnl']:+7.1f}%")
