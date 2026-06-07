import ccxt
import pandas as pd
import numpy as np
import time
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *
from strategy import detect_elephant_bars, detect_wick_bars, calculate_indicators
from patterns import detect_all_patterns


def fetch_ohlcv(symbol, timeframe, days=60):
    """Busca dados historicos"""
    exchange = ccxt.binance({'enableRateLimit': True})
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=days)).isoformat())
    data = []
    while True:
        d = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not d:
            break
        data.extend(d)
        since = d[-1][0] + 1
        if len(d) < 1000:
            break
        time.sleep(0.1)
    df = pd.DataFrame(data, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df.set_index('ts', inplace=True)
    return df


def sim_exit(df, entry_idx, stop, target, n, direction):
    """Simula saida"""
    for k in range(entry_idx + 1, min(entry_idx + 100, n)):
        bar = df.iloc[k]
        if direction == 'buy':
            if bar['l'] <= stop:
                return stop, 'SL', k - entry_idx
            if bar['h'] >= target:
                return target, 'TP', k - entry_idx
        else:
            if bar['h'] >= stop:
                return stop, 'SL', k - entry_idx
            if bar['l'] <= target:
                return target, 'TP', k - entry_idx
    end = min(entry_idx + 100, n - 1)
    return df.iloc[end]['c'], 'TO', end - entry_idx


def calculate_stop_dist(entry_price, high, low, direction):
    """Calcula stop"""
    bar_range = high - low
    if STOP_MODE == 'half':
        stop_dist = bar_range * 0.5
    elif STOP_MODE == 'full':
        stop_dist = bar_range
    else:
        stop_dist = bar_range * 0.1

    if direction == 'buy':
        return entry_price - stop_dist
    else:
        return entry_price + stop_dist


def calculate_target(entry, stop, direction):
    """Calcula target"""
    risk = abs(entry - stop)
    if direction == 'buy':
        return entry + risk * RR_RATIO
    else:
        return entry - risk * RR_RATIO


def run_backtest(df, strategy='all'):
    """
    Executa backtest.
    strategy: 'elephant', 'wick', 'patterns', ou 'all'
    """
    df = calculate_indicators(df)
    n = len(df)
    trades = []

    elephants = detect_elephant_bars(df)
    wicks = detect_wick_bars(df)
    patterns = detect_all_patterns(df)

    H = df['h'].values
    L = df['l'].values

    items = []
    if strategy in ('elephant', 'all'):
        items.extend(elephants)
    if strategy in ('wick', 'all'):
        items.extend(wicks)

    # Processar elephant/wick (entry na proxima barra)
    for item in items:
        i = item['index']
        if i + 2 >= n:
            continue

        entry_idx = i + 1
        if entry_idx >= n:
            continue

        if item['type'] == 'elephant':
            direction = 'buy' if item['is_bull'] else 'sell'
            entry_price = H[i] if direction == 'buy' else L[i]
        else:
            direction = 'buy' if item['wick_type'] == 'bull_wick' else 'sell'
            entry_price = H[i] if direction == 'buy' else L[i]

        stop = calculate_stop_dist(entry_price, H[i], L[i], direction)
        target = calculate_target(entry_price, stop, direction)

        if direction == 'buy' and H[entry_idx] <= H[i]:
            continue
        if direction == 'sell' and L[entry_idx] >= L[i]:
            continue

        exit_price, reason, bars_held = sim_exit(df, entry_idx, stop, target, n, direction)

        if direction == 'buy':
            pnl = ((exit_price - entry_price) / entry_price * 100)
        else:
            pnl = ((entry_price - exit_price) / entry_price * 100)

        if item['type'] == 'elephant':
            label = 'E+_' if item.get('is_plus', False) else 'E_'
            label += '1st' if item.get('is_first', True) else '2nd+'
            label += '_Bull' if item['is_bull'] else '_Bear'
        else:
            label = 'Wick_Bull' if item['wick_type'] == 'bull_wick' else 'Wick_Bear'

        trades.append({
            'et': df.index[entry_idx], 'ep': entry_price, 'pnl': pnl,
            'xr': reason, 'bh': bars_held, 'pt': label, 'bull': direction == 'buy'
        })

    # Processar padroes complexos (entry/stop/target ja definidos)
    if strategy in ('patterns', 'all'):
        for pat in patterns:
            idx = pat['index']
            if idx >= n:
                continue

            entry_price = pat['entry']
            stop = pat['stop']
            target = pat['target']
            direction = pat['direction']

            # Entry na barra do sinal
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

    trades.sort(key=lambda x: x['et'])
    return trades


def calc_metrics(trades, initial_capital=10000):
    """Calcula metricas"""
    if not trades:
        return None

    d = pd.DataFrame(trades)
    w = d[d['pnl'] > 0]
    l = d[d['pnl'] <= 0]

    eq = initial_capital
    pk = initial_capital
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


def main():
    symbols = SYMBOLS if 'SYMBOLS' in dir() else ["BTC/USDT", "ETH/USDT"]
    timeframes = ["3m", "5m", "15m", "30m", "1h"]
    days = 60

    print(f"\n{'='*70}")
    print(f"  BACKTEST - ELEPHANT + WICK BAR")
    print(f"  Stop: {STOP_MODE} | R:R 1:{RR_RATIO} | {days} dias")
    print(f"{'='*70}\n")

    all_results = {}

    for sym in symbols:
        for tf in timeframes:
            key = f"{sym}_{tf}"
            print(f"  {sym} {tf}...", end=" ", flush=True)
            try:
                df = fetch_ohlcv(sym, tf, days)
                m_ele = calc_metrics(run_backtest(df, 'elephant'))
                m_wick = calc_metrics(run_backtest(df, 'wick'))
                m_all = calc_metrics(run_backtest(df, 'all'))
                all_results[key] = {'elephant': m_ele, 'wick': m_wick, 'all': m_all}
                print(f"{len(df)}b OK")
            except Exception as e:
                print(f"ERRO: {e}")
                all_results[key] = None

    # Tabela
    print(f"\n{'='*70}")
    print(f"  RESULTADOS")
    print(f"{'='*70}")
    print(f"\n  {'Ativo/TF':<15} {'Modo':<10} {'T':>5} {'T/dia':>6} {'WR%':>6} {'PnL%':>8} {'PF':>5} {'MDD%':>6} {'$Final':>10}")
    print(f"  {'-'*75}")

    for key, res in all_results.items():
        if not res:
            continue
        for mode in ['elephant', 'wick', 'all']:
            m = res[mode]
            if m and m['t'] > 0:
                tpd = round(m['t'] / days, 1)
                print(f"  {key:<15} {mode:<10} {m['t']:>5} {tpd:>5.1f} {m['wr']:>5.1f}% {m['pnl']:>7.1f}% {m['pf']:>5.2f} {m['mdd']:>5.1f}% ${m['final']:>9,.0f}")
        print()

    # Detalhes
    print(f"\n{'='*70}")
    print(f"  DETALHES POR TIPO")
    print(f"{'='*70}")

    for key, res in all_results.items():
        if not res or not res['all']:
            continue
        print(f"\n  {key}:")
        for pt, data in res['all']['by_type'].items():
            print(f"    {pt}: {data['n']} trades | WR: {data['wr']}% | PnL: {data['pnl']}%")

    print(f"\n  Capital: $10,000 | R:R 1:{RR_RATIO} | Stop: {STOP_MODE}")


if __name__ == '__main__':
    main()
