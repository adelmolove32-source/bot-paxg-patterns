import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

from config import *
from backtest import fetch_ohlcv, calculate_stop_dist, calculate_target
from strategy import calculate_indicators, detect_elephant_bars, detect_wick_bars
from patterns import detect_all_patterns


CAPITAL = 200
MAX_POSITIONS = 1
POSITION_PCT = 0.333
FIXED_ENTRY = 66.67
DAYS = 60
MIN_TARGET_PCT = 0.5


def sim_exit_realistic(df, entry_idx, stop, target, n, direction, max_bars=100):
    """Simula saida verificando high/low de cada barra"""
    for k in range(entry_idx + 1, min(entry_idx + max_bars, n)):
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
    end = min(entry_idx + max_bars, n - 1)
    return df.iloc[end]['c'], 'TO', end - entry_idx


def run_realistic_backtest(df):
    """Backtest com gestao real de capital"""
    df = calculate_indicators(df)
    n = len(df)
    
    elephants = detect_elephant_bars(df)
    wicks = detect_wick_bars(df)
    patterns = detect_all_patterns(df)
    
    H = df['h'].values
    L = df['l'].values
    
    # Juntar todos os sinais
    all_signals = []
    
    for item in elephants:
        i = item['index']
        if i + 2 >= n:
            continue
        entry_idx = i + 1
        if entry_idx >= n:
            continue
        
        direction = 'buy' if item['is_bull'] else 'sell'
        entry_price = H[i] if direction == 'buy' else L[i]
        stop = calculate_stop_dist(entry_price, H[i], L[i], direction)
        target = calculate_target(entry_price, stop, direction)
        
        # Filtro target minimo
        target_pct = abs(target - entry_price) / entry_price * 100
        if target_pct < MIN_TARGET_PCT:
            continue
        
        if direction == 'buy' and H[entry_idx] <= H[i]:
            continue
        if direction == 'sell' and L[entry_idx] >= L[i]:
            continue
        
        label = 'E+_' if item.get('is_plus', False) else 'E_'
        label += '1st' if item.get('is_first', True) else '2nd+'
        label += '_Bull' if item['is_bull'] else '_Bear'
        
        all_signals.append({
            'index': entry_idx,
            'direction': direction,
            'entry': entry_price,
            'stop': stop,
            'target': target,
            'label': label,
            'type': 'elephant'
        })
    
    for item in wicks:
        i = item['index']
        if i + 2 >= n:
            continue
        entry_idx = i + 1
        if entry_idx >= n:
            continue
        
        direction = 'buy' if item['wick_type'] == 'bull_wick' else 'sell'
        entry_price = H[i] if direction == 'buy' else L[i]
        stop = calculate_stop_dist(entry_price, H[i], L[i], direction)
        target = calculate_target(entry_price, stop, direction)
        
        # Filtro target minimo
        target_pct = abs(target - entry_price) / entry_price * 100
        if target_pct < MIN_TARGET_PCT:
            continue
        
        if direction == 'buy' and H[entry_idx] <= H[i]:
            continue
        if direction == 'sell' and L[entry_idx] >= L[i]:
            continue
        
        label = 'Wick_Bull' if item['wick_type'] == 'bull_wick' else 'Wick_Bear'
        
        all_signals.append({
            'index': entry_idx,
            'direction': direction,
            'entry': entry_price,
            'stop': stop,
            'target': target,
            'label': label,
            'type': 'wick'
        })
    
    for pat in patterns:
        if pat['index'] >= n:
            continue
        
        # Filtro target minimo
        target_pct = abs(pat['target'] - pat['entry']) / pat['entry'] * 100
        if target_pct < MIN_TARGET_PCT:
            continue
        
        all_signals.append({
            'index': pat['index'],
            'direction': pat['direction'],
            'entry': pat['entry'],
            'stop': pat['stop'],
            'target': pat['target'],
            'label': pat['label'],
            'type': 'pattern'
        })
    
    all_signals.sort(key=lambda x: x['index'])
    
    # Simulacao com gestao de capital
    capital = CAPITAL
    peak_capital = CAPITAL
    max_drawdown = 0
    open_positions = []
    closed_trades = []
    
    for sig in all_signals:
        idx = sig['index']
        if idx >= n:
            continue
        
        # Fechar posicoes que atingiram stop/target
        i = 0
        while i < len(open_positions):
            pos = open_positions[i]
            exit_price, reason, bars = sim_exit_realistic(
                df, pos['entry_idx'], pos['stop'], pos['target'], n, pos['direction']
            )
            
            if pos['direction'] == 'buy':
                pnl_pct = (exit_price - pos['entry']) / pos['entry'] * 100
            else:
                pnl_pct = (pos['entry'] - exit_price) / pos['entry'] * 100
            
            pnl_usd = pos['entry_usd'] * pnl_pct / 100
            capital += pnl_usd
            
            if capital > peak_capital:
                peak_capital = capital
            dd = (peak_capital - capital) / peak_capital * 100
            if dd > max_drawdown:
                max_drawdown = dd
            
            closed_trades.append({
                'label': pos['label'],
                'direction': pos['direction'],
                'pnl_pct': round(pnl_pct, 2),
                'pnl_usd': round(pnl_usd, 2),
                'reason': reason,
                'capital_after': round(capital, 2)
            })
            
            open_positions.pop(i)
        
        # Abrir nova posicao se tem espaco
        if len(open_positions) < MAX_POSITIONS and capital > 10:
            entry_usd = FIXED_ENTRY
            qty = entry_usd / sig['entry']
            
            open_positions.append({
                'entry_idx': idx,
                'entry': sig['entry'],
                'stop': sig['stop'],
                'target': sig['target'],
                'direction': sig['direction'],
                'label': sig['label'],
                'entry_usd': round(entry_usd, 2),
                'qty': qty
            })
    
    # Fechar posicoes restantes
    for pos in open_positions:
        exit_price, reason, bars = sim_exit_realistic(
            df, pos['entry_idx'], pos['stop'], pos['target'], n, pos['direction']
        )
        
        if pos['direction'] == 'buy':
            pnl_pct = (exit_price - pos['entry']) / pos['entry'] * 100
        else:
            pnl_pct = (pos['entry'] - exit_price) / pos['entry'] * 100
        
        pnl_usd = pos['entry_usd'] * pnl_pct / 100
        capital += pnl_usd
        
        closed_trades.append({
            'label': pos['label'],
            'direction': pos['direction'],
            'pnl_pct': round(pnl_pct, 2),
            'pnl_usd': round(pnl_usd, 2),
            'reason': reason,
            'capital_after': round(capital, 2)
        })
    
    return closed_trades, capital, max_drawdown


def calc_metrics_realistic(trades, capital_start, capital_end, max_dd):
    """Calcula metricas do backtest realista"""
    if not trades:
        return None
    
    wins = [t for t in trades if t['pnl_usd'] > 0]
    losses = [t for t in trades if t['pnl_usd'] <= 0]
    
    total_pnl = sum(t['pnl_usd'] for t in trades)
    total_pnl_pct = (capital_end - capital_start) / capital_start * 100
    
    win_sum = sum(t['pnl_usd'] for t in wins)
    loss_sum = abs(sum(t['pnl_usd'] for t in losses))
    pf = win_sum / loss_sum if loss_sum > 0 else 999
    
    by_label = {}
    for t in trades:
        label = t['label']
        if label not in by_label:
            by_label[label] = {'n': 0, 'wins': 0, 'pnl': 0}
        by_label[label]['n'] += 1
        if t['pnl_usd'] > 0:
            by_label[label]['wins'] += 1
        by_label[label]['pnl'] += t['pnl_usd']
    
    for k in by_label:
        by_label[k]['wr'] = round(by_label[k]['wins'] / by_label[k]['n'] * 100, 1) if by_label[k]['n'] > 0 else 0
        by_label[k]['pnl'] = round(by_label[k]['pnl'], 2)
    
    return {
        'trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'wr': round(len(wins) / len(trades) * 100, 1),
        'pnl_usd': round(total_pnl, 2),
        'pnl_pct': round(total_pnl_pct, 2),
        'pf': round(min(pf, 999), 2),
        'mdd': round(max_dd, 2),
        'capital_end': round(capital_end, 2),
        'by_label': by_label
    }


def main():
    print(f"\n{'='*70}")
    print(f"  BACKTEST REALISTA - $200 | 3 entradas | R:R 1:3 | {DAYS} dias")
    print(f"{'='*70}")
    
    for symbol in ['BTC/USDT', 'ETH/USDT']:
        for tf in ['3m', '5m']:
            print(f"\n  Buscando {symbol} {tf}...")
            df = fetch_ohlcv(symbol, tf, days=DAYS)
            print(f"  {len(df)} barras, rodando backtest realista...")
            
            trades, capital_end, max_dd = run_realistic_backtest(df)
            
            if not trades:
                print(f"  {symbol} {tf}: 0 trades")
                continue
            
            m = calc_metrics_realistic(trades, CAPITAL, capital_end, max_dd)
            per_day = m['trades'] / DAYS
            
            print(f"\n  {symbol} {tf}: {m['trades']} trades ({per_day:.0f}/dia)")
            print(f"  Capital: ${CAPITAL} -> ${m['capital_end']}")
            print(f"  PnL: ${m['pnl_usd']:+.2f} ({m['pnl_pct']:+.2f}%)")
            print(f"  WR: {m['wr']}% | PF: {m['pf']} | MDD: {m['mdd']}%")
            
            print(f"\n  Top padroes:")
            sorted_labels = sorted(m['by_label'].items(), key=lambda x: x[1]['pnl'], reverse=True)
            for label, data in sorted_labels[:8]:
                print(f"    {label:20s}: {data['n']:4d} trades | WR: {data['wr']:5.1f}% | PnL: ${data['pnl']:+8.2f}")
    
    print(f"\n{'='*70}")
    print(f"  Capital: ${CAPITAL} | Posicoes: {MAX_POSITIONS} | Entrada: {POSITION_PCT*100:.1f}%")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
