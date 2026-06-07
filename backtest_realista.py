"""
BACKTEST REALISTA - Max 3 posicoes simultaneas, 50% cada | 60 dias
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


def run_backtest_realistic(df):
    """Backtest com posicoes simultaneas e tamanho fracionado"""
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

        # 1. FECHAR posicoes que bateram SL ou TP
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
                # Calcular PnL real (baseado no tamanho da posicao)
                position_value = pos['position_value']
                if pos['direction'] == 'buy':
                    pnl_pct = (exit_price - pos['entry']) / pos['entry'] * 100
                else:
                    pnl_pct = (pos['entry'] - exit_price) / pos['entry'] * 100

                pnl_usd = position_value * pnl_pct / 100
                balance += pnl_usd

                # Atualizar drawdown
                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance * 100
                if dd > max_drawdown:
                    max_drawdown = dd

                closed_trades.append({
                    'et': pos['open_time'], 'ep': pos['entry'],
                    'pnl_real': round(pnl_pct, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'xr': reason, 'pt': pos['label'],
                    'pos_size': round(position_value, 2),
                    'exit_price': exit_price
                })
                open_positions.pop(i)
            else:
                i += 1

        # 2. ABRIR novas posicoes se houver sinal e espaco
        if len(open_positions) < MAX_POSITIONS and balance > 10:
            for pat in patterns:
                if pat['index'] != bar_idx:
                    continue
                if len(open_positions) >= MAX_POSITIONS:
                    break

                # Verificar se ja tem posicao nesse symbol+direction
                direction = pat['direction']
                entry = pat['entry']
                stop = pat['stop']
                target = pat['target']

                # Calcular tamanho da posicao (50% do saldo)
                position_value = balance * POSITION_SIZE_PCT
                if position_value < 1:
                    continue

                open_positions.append({
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'direction': direction,
                    'label': pat['label'],
                    'position_value': position_value,
                    'open_time': bar_time
                })

        # 3. Fechar posicoes por timeout (100 barras)
        i = 0
        while i < len(open_positions):
            pos = open_positions[i]
            bars_open = bar_idx - df.index.get_loc(pos['open_time']) if pos['open_time'] in df.index else 0
            if bars_open >= 100:
                # Fechar pelo preco de fechamento
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
                    'pnl_real': round(pnl_pct, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'xr': 'TIMEOUT', 'pt': pos['label'],
                    'pos_size': round(position_value, 2),
                    'exit_price': exit_price
                })
                open_positions.pop(i)
            else:
                i += 1

    # Fechar posicoes restantes pelo preco final
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
            'pnl_real': round(pnl_pct, 2),
            'pnl_usd': round(pnl_usd, 2),
            'xr': 'END', 'pt': pos['label'],
            'pos_size': round(position_value, 2),
            'exit_price': exit_price
        })

    return closed_trades, balance, max_drawdown


def calc_metrics(trades, final_balance, mdd):
    """Calcula metricas"""
    if not trades:
        return None

    d = pd.DataFrame(trades)
    w = d[d['pnl_usd'] > 0]
    l = d[d['pnl_usd'] <= 0]

    total_pnl_usd = d['pnl_usd'].sum()
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
        'pnl_usd': round(total_pnl_usd, 2),
        'pnl_pct': round(total_pnl_pct, 2),
        'pf': round(min(pf, 999), 2),
        'mdd': round(mdd, 2),
        'final': round(final_balance, 2),
        'by_type': by_type
    }


# =============================================================================
# RODAR BACKTEST
# =============================================================================
print(f"\n{'='*75}")
print(f"  BACKTEST REALISTA - Max 3 posicoes | 50% cada | R:R 1:3 | {DAYS} dias")
print(f"  Banca: ${INITIAL_CAPITAL}")
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
        trades, final_bal, mdd = run_backtest_realistic(df)
        if not trades:
            print("0 trades")
            continue
        m = calc_metrics(trades, final_bal, mdd)
        per_day = m['t'] / DAYS
        print(f"{m['t']} trades ({per_day:.1f}/dia) | WR: {m['wr']}% | PnL: {m['pnl_pct']:+.2f}% (${m['pnl_usd']:+.0f}) | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}% | ${INITIAL_CAPITAL} -> ${m['final']:,.0f}")
        results.append({
            'par': sym, 'tf': tf, 'trades': m['t'], 'per_day': per_day,
            'wr': m['wr'], 'pnl_pct': m['pnl_pct'], 'pnl_usd': m['pnl_usd'],
            'pf': m['pf'], 'mdd': m['mdd'], 'final': m['final'],
            'by_type': m['by_type']
        })
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

# =============================================================================
# RANKING
# =============================================================================
print(f"\n{'='*75}")
print(f"  RANKING - BACKTEST REALISTA (ordenado por lucro)")
print(f"{'='*75}")
print(f"\n  {'#':>2} {'Par/TF':<15} {'T':>5} {'T/dia':>6} {'WR%':>6} {'PnL%':>8} {'PF':>5} {'MDD%':>6} {'$200->':>8}")
print(f"  {'-'*70}")

results.sort(key=lambda x: x['pnl_pct'], reverse=True)
for i, r in enumerate(results, 1):
    print(f"  {i:>2}o {r['par']+'/'+r['tf']:<15} {r['trades']:>5} {r['per_day']:>5.1f} {r['wr']:>5.1f}% {r['pnl_pct']:>7.1f}% {r['pf']:>5.2f} {r['mdd']:>5.1f}% ${r['final']:>7,.0f}")

# Detalhes top 3
print(f"\n{'='*75}")
print(f"  TOP 3 - DETALHES POR PATTERN")
print(f"{'='*75}")

for r in results[:3]:
    print(f"\n  {r['par']}/{r['tf']} - PnL: {r['pnl_pct']:+.1f}% | ${INITIAL_CAPITAL} -> ${r['final']:,.0f}")
    sorted_pt = sorted(r['by_type'].items(), key=lambda x: x[1]['pnl_usd'], reverse=True)
    for pt, data in sorted_pt:
        if data['n'] >= 3:
            print(f"    {pt:20s}: {data['n']:3d} trades | WR: {data['wr']:5.1f}% | PnL: ${data['pnl_usd']:+7.0f}")

# Comparacao
print(f"\n{'='*75}")
print(f"  COMPARACAO: Backtest Simples vs Realista")
print(f"{'='*75}")
print(f"\n  {'Par/TF':<15} {'Simples':>12} {'Realista':>12} {'Diferenca':>10}")
print(f"  {'-'*50}")

# Dados do backtest simples (do arquivo anterior)
simple_results = {
    'BTC/USDT/3m': 16.0, 'BTC/USDT/5m': 29.7, 'BTC/USDT/15m': 90.6,
    'ETH/USDT/3m': 57.9, 'ETH/USDT/5m': 14.2, 'ETH/USDT/15m': 76.6,
}

for r in results:
    key = f"{r['par']}/{r['tf']}"
    simple = simple_results.get(key, 0)
    diff = r['pnl_pct'] - simple
    print(f"  {key:<15} {simple:>+11.1f}% {r['pnl_pct']:>+11.1f}% {diff:>+9.1f}%")
