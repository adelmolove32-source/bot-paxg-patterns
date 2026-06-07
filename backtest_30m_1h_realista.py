import sys, os
sys.path.insert(0, r'C:\Users\muril\Desktop\bot btc4')
os.chdir(r'C:\Users\muril\Desktop\bot btc4')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest import fetch_ohlcv, sim_exit, calculate_stop_dist, calculate_target
from config import RR_RATIO, STOP_MODE
from strategy import calculate_indicators
from patterns import detect_all_patterns

DAYS = 60
POSITION_SIZE_PCT = 0.5
MAX_POSITIONS = 3
INITIAL_CAPITAL = 200

def run_backtest_realistic_local(df):
    df = calculate_indicators(df)
    n = len(df)
    patterns = detect_all_patterns(df)
    H = df['h'].values
    L = df['l'].values
    C = df['c'].values
    balance = INITIAL_CAPITAL
    peak_balance = INITIAL_CAPITAL
    max_drawdown = 0
    open_positions = []
    closed_trades = []
    for bar_idx in range(n):
        bar_time = df.index[bar_idx]
        high = H[bar_idx]
        low = L[bar_idx]
        i = 0
        while i < len(open_positions):
            pos = open_positions[i]
            exit_price = None
            reason = None
            if pos['direction'] == 'buy':
                if low <= pos['stop']:
                    exit_price = pos['stop']
                    reason = 'SL'
                elif high >= pos['target']:
                    exit_price = pos['target']
                    reason = 'TP'
            else:
                if high >= pos['stop']:
                    exit_price = pos['stop']
                    reason = 'SL'
                elif low <= pos['target']:
                    exit_price = pos['target']
                    reason = 'TP'
            if exit_price:
                position_value = pos['position_value']
                if pos['direction'] == 'buy':
                    pnl_pct = (exit_price - pos['entry']) / pos['entry'] * 100
                else:
                    pnl_pct = (pos['entry'] - exit_price) / pos['entry'] * 100
                pnl_usd = position_value * pnl_pct / 100
                balance += pnl_usd
                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance * 100
                if dd > max_drawdown:
                    max_drawdown = dd
                closed_trades.append({
                    'et': pos['open_time'], 'ep': pos['entry'],
                    'pnl_real': round(pnl_pct, 2), 'pnl_usd': round(pnl_usd, 2),
                    'xr': reason, 'pt': pos['label'],
                    'pos_size': round(position_value, 2), 'exit_price': exit_price
                })
                open_positions.pop(i)
            else:
                i += 1
        if len(open_positions) < MAX_POSITIONS and balance > 10:
            for pat in patterns:
                if pat['index'] != bar_idx:
                    continue
                if len(open_positions) >= MAX_POSITIONS:
                    break
                direction = pat['direction']
                entry = pat['entry']
                stop = pat['stop']
                target = pat['target']
                position_value = balance * POSITION_SIZE_PCT
                if position_value < 1:
                    continue
                open_positions.append({
                    'entry': entry, 'stop': stop, 'target': target,
                    'direction': direction, 'label': pat['label'],
                    'position_value': position_value, 'open_time': bar_time
                })
        i = 0
        while i < len(open_positions):
            pos = open_positions[i]
            bars_open = bar_idx - df.index.get_loc(pos['open_time']) if pos['open_time'] in df.index else 0
            if bars_open >= 100:
                exit_price = C[bar_idx]
                position_value = pos['position_value']
                if pos['direction'] == 'buy':
                    pnl_pct = (exit_price - pos['entry']) / pos['entry'] * 100
                else:
                    pnl_pct = (pos['entry'] - exit_price) / pos['entry'] * 100
                pnl_usd = position_value * pnl_pct / 100
                balance += pnl_usd
                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance * 100
                if dd > max_drawdown:
                    max_drawdown = dd
                closed_trades.append({
                    'et': pos['open_time'], 'ep': pos['entry'],
                    'pnl_real': round(pnl_pct, 2), 'pnl_usd': round(pnl_usd, 2),
                    'xr': 'TIMEOUT', 'pt': pos['label'],
                    'pos_size': round(position_value, 2), 'exit_price': exit_price
                })
                open_positions.pop(i)
            else:
                i += 1
    for pos in open_positions:
        exit_price = C[-1]
        position_value = pos['position_value']
        if pos['direction'] == 'buy':
            pnl_pct = (exit_price - pos['entry']) / pos['entry'] * 100
        else:
            pnl_pct = (pos['entry'] - exit_price) / pos['entry'] * 100
        pnl_usd = position_value * pnl_pct / 100
        balance += pnl_usd
        closed_trades.append({
            'et': pos['open_time'], 'ep': pos['entry'],
            'pnl_real': round(pnl_pct, 2), 'pnl_usd': round(pnl_usd, 2),
            'xr': 'END', 'pt': pos['label'],
            'pos_size': round(position_value, 2), 'exit_price': exit_price
        })
    return closed_trades, balance, max_drawdown

def calc_metrics_local(trades, final_balance, mdd):
    if not trades:
        return None
    d = pd.DataFrame(trades)
    w = d[d['pnl_usd'] > 0]
    l = d[d['pnl_usd'] <= 0]
    total_pnl_pct = (final_balance - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    win_sum = w['pnl_usd'].sum() if len(w) > 0 else 0
    loss_sum = abs(l['pnl_usd'].sum()) if len(l) > 0 else 0
    pf = win_sum / loss_sum if loss_sum > 0 else 999
    by_type = {}
    for pt in d['pt'].unique():
        sub = d[d['pt'] == pt]
        sw = sub[sub['pnl_usd'] > 0]
        by_type[pt] = {
            'n': len(sub),
            'wr': round(len(sw) / len(sub) * 100, 1) if len(sub) > 0 else 0,
            'pnl_usd': round(sub['pnl_usd'].sum(), 2)
        }
    return {
        't': len(d), 'w': len(w), 'l': len(l),
        'wr': round(len(w) / len(d) * 100, 1),
        'pnl_pct': round(total_pnl_pct, 2),
        'pf': round(min(pf, 999), 2),
        'mdd': round(mdd, 2),
        'final': round(final_balance, 2),
        'by_type': by_type
    }

print(f"\n{'='*75}")
print(f"  BACKTEST REALISTA - Max 3 pos | 50% cada | R:R 1:3 | 60 dias | $200")
print(f"  30m e 1h")
print(f"{'='*75}\n")

for sym, tf in [('BTC/USDT','30m'), ('BTC/USDT','1h'), ('ETH/USDT','30m'), ('ETH/USDT','1h')]:
    print(f'{sym} {tf}...', end=' ', flush=True)
    try:
        df = fetch_ohlcv(sym, tf, days=DAYS)
        trades, final_bal, mdd = run_backtest_realistic_local(df)
        if not trades:
            print('0 trades')
            continue
        m = calc_metrics_local(trades, final_bal, mdd)
        per_day = m['t'] / DAYS
        print(f"{m['t']} trades ({per_day:.1f}/dia) | WR: {m['wr']}% | PnL: {m['pnl_pct']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}% | $200 -> ${m['final']:,.0f}")
        sorted_pt = sorted(m['by_type'].items(), key=lambda x: x[1]['pnl_usd'], reverse=True)
        for pt, data in sorted_pt:
            if data['n'] >= 3:
                print(f"  {pt:20s}: {data['n']:3d} trades | WR: {data['wr']:5.1f}% | PnL: ${data['pnl_usd']:+7.0f}")
    except Exception as e:
        print(f'ERRO: {e}')

