import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from backtest import run_backtest, calc_metrics, fetch_ohlcv
from patterns import detect_all_patterns
from strategy import calculate_indicators

def run_backtest_filtered(df, min_body_ratio=None, only_bull=False, only_bear=False, 
                          min_rr=None, max_trades_per_day=None):
    """Backtest com filtros"""
    df = calculate_indicators(df)
    patterns = detect_all_patterns(df)
    n = len(df)
    
    trades = []
    last_trade_idx = -999
    min_bars_between = 5
    
    H = df['h'].values
    L = df['l'].values
    
    for pat in patterns:
        idx = pat['index']
        if idx >= n:
            continue
        
        # Filtro: so bull ou bear
        if only_bull and pat['direction'] == 'sell':
            continue
        if only_bear and pat['direction'] == 'buy':
            continue
        
        # Filtro: distancia minima entre trades
        if idx - last_trade_idx < min_bars_between:
            continue
        
        # Filtro: corpo minimo da barra
        if min_body_ratio:
            body = abs(df['c'].iloc[idx] - df['o'].iloc[idx])
            rng = H[idx] - L[idx]
            if rng > 0 and (body / rng) < min_body_ratio:
                continue
        
        entry_price = pat['entry']
        stop = pat['stop']
        target = pat['target']
        direction = pat['direction']
        
        # Calcular R:R real do sinal
        risk = abs(entry_price - stop)
        reward = abs(target - entry_price)
        if risk > 0:
            rr = reward / risk
        else:
            rr = 0
        
        # Filtro: R:R minimo
        if min_rr and rr < min_rr:
            continue
        
        from backtest import sim_exit
        exit_price, reason, bars_held = sim_exit(df, idx, stop, target, n, direction)
        
        if direction == 'buy':
            pnl = ((exit_price - entry_price) / entry_price * 100)
        else:
            pnl = ((entry_price - exit_price) / entry_price * 100)
        
        trades.append({
            'et': df.index[idx], 'ep': entry_price, 'pnl': pnl,
            'xr': reason, 'bh': bars_held, 'pt': pat['label'],
            'bull': direction == 'buy'
        })
        
        last_trade_idx = idx
    
    return trades


days = 60

print(f"\n{'='*70}")
print(f"  TESTE DE FILTROS - PATTERNS | {days} dias")
print(f"{'='*70}")

for sym in ['BTC/USDT', 'ETH/USDT']:
    for tf in ['30m', '15m']:
        df = fetch_ohlcv(sym, tf, days=days)
        
        print(f"\n  {'='*60}")
        print(f"  {sym} {tf}")
        print(f"  {'='*60}")
        
        # Baseline (sem filtro)
        trades = run_backtest_filtered(df)
        m = calc_metrics(trades)
        print(f"\n  BASELINE:     {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 1: So signals com corpo > 50%
        trades = run_backtest_filtered(df, min_body_ratio=0.5)
        m = calc_metrics(trades)
        if m:
            print(f"  Body>50%:     {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 2: So bull
        trades = run_backtest_filtered(df, only_bull=True)
        m = calc_metrics(trades)
        if m:
            print(f"  So Bull:      {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 3: So bear
        trades = run_backtest_filtered(df, only_bear=True)
        m = calc_metrics(trades)
        if m:
            print(f"  So Bear:      {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 4: R:R > 2
        trades = run_backtest_filtered(df, min_rr=2.0)
        m = calc_metrics(trades)
        if m:
            print(f"  R:R>2:        {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 5: Body>50% + R:R>2
        trades = run_backtest_filtered(df, min_body_ratio=0.5, min_rr=2.0)
        m = calc_metrics(trades)
        if m:
            print(f"  Body>50%+RR2: {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 6: So Bull + Body>50%
        trades = run_backtest_filtered(df, only_bull=True, min_body_ratio=0.5)
        m = calc_metrics(trades)
        if m:
            print(f"  Bull+Body:    {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 7: So Bear + Body>50%
        trades = run_backtest_filtered(df, only_bear=True, min_body_ratio=0.5)
        m = calc_metrics(trades)
        if m:
            print(f"  Bear+Body:    {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 8: Body>60%
        trades = run_backtest_filtered(df, min_body_ratio=0.6)
        m = calc_metrics(trades)
        if m:
            print(f"  Body>60%:     {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
        
        # Filtro 9: R:R > 3
        trades = run_backtest_filtered(df, min_rr=3.0)
        m = calc_metrics(trades)
        if m:
            print(f"  R:R>3:        {m['t']:4d} trades ({m['t']/days:.0f}/dia) | WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%")
