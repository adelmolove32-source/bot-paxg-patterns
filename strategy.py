import numpy as np
import pandas as pd
from config import *
from patterns import detect_all_patterns


class Signal:
    """Sinal de entrada"""
    def __init__(self, signal_type, direction, index, price, stop, bar_range, label):
        self.type = signal_type
        self.direction = direction
        self.index = index
        self.price = price
        self.stop = stop
        self.bar_range = bar_range
        self.label = label

    def __repr__(self):
        return f"Signal({self.label} {self.direction} @ {self.price:.2f})"


def calculate_indicators(df):
    """Calcula indicadores"""
    df = df.copy()
    df['body'] = abs(df['c'] - df['o'])
    df['rng'] = (df['h'] - df['l']).replace(0, np.nan)
    df['avg_rng'] = df['rng'].rolling(10).mean()
    df['solid'] = (df['body'] / df['rng']) > ELEPHANT_BODY_PCT
    df['green'] = df['c'] > df['o']
    df['wick_up'] = df['h'] - df[['o', 'c']].max(axis=1)
    df['wick_dn'] = df[['o', 'c']].min(axis=1) - df['l']
    df['ema20'] = df['c'].ewm(span=20, adjust=False).mean()
    return df


def detect_elephant_bars(df):
    """Detecta barras elefante com filtros"""
    n = len(df)
    if n < ELEPHANT_LOOKBACK + 5:
        return []

    O = df['o'].values
    C = df['c'].values
    H = df['h'].values
    L = df['l'].values
    RNG = df['rng'].values
    AR = df['avg_rng'].values
    EMA = df['ema20'].values

    elephants = []
    last_signal_idx = -999

    for i in range(ELEPHANT_LOOKBACK + 5, n):
        if np.isnan(AR[i]) or AR[i] == 0:
            continue

        # Filtro de cooldown
        if i - last_signal_idx < MIN_BARS_BETWEEN:
            continue

        bar_rng = H[i] - L[i]
        if bar_rng == 0:
            continue

        # 1. Barra >= MIN_BAR_RATIO (2.0x por padrao)
        if bar_rng < AR[i] * MIN_BAR_RATIO:
            continue

        # 2. Corpo solido
        body = abs(C[i] - O[i])
        if body / bar_rng < ELEPHANT_BODY_PCT:
            continue

        is_bull = C[i] > O[i]

        # 3. Filtro EMA20: so comprar se preco > EMA20, so vender se < EMA20
        if EMA20_FILTER:
            if is_bull and C[i] < EMA[i]:
                continue
            if not is_bull and C[i] > EMA[i]:
                continue

        # 4. Primeira elefante
        left_max = RNG[max(0, i - ELEPHANT_LOOKBACK):i].max()
        is_first = bar_rng > left_max * 1.2 if left_max > 0 else True

        if ONLY_FIRST_ELEPHANT and not is_first:
            continue

        # 5. Elephant Plus
        if is_bull:
            is_plus = C[i] >= H[i] - bar_rng * ELEPHANT_PLUS_TOP
        else:
            is_plus = L[i] <= L[i] + bar_rng * ELEPHANT_PLUS_TOP
        if is_plus:
            remaining = (C[i] - L[i]) if is_bull else (H[i] - O[i])
            is_plus = remaining >= AR[i] * MIN_BAR_RATIO

        last_signal_idx = i
        elephants.append({
            'index': i,
            'type': 'elephant',
            'is_bull': is_bull,
            'is_first': is_first,
            'is_plus': is_plus,
            'bar_rng': bar_rng,
            'high': H[i],
            'low': L[i],
            'open': O[i],
            'close': C[i]
        })

    return elephants


def detect_wick_bars(df):
    """Detecta barras de pavio com filtros"""
    n = len(df)
    if n < 10:
        return []

    H = df['h'].values
    L = df['l'].values
    O = df['o'].values
    C = df['c'].values
    BODY = df['body'].values
    WU = df['wick_up'].values
    WD = df['wick_dn'].values
    RNG = df['rng'].values
    EMA = df['ema20'].values

    wicks = []
    last_signal_idx = -999

    for i in range(5, n):
        if np.isnan(RNG[i]) or RNG[i] == 0:
            continue

        # Cooldown
        if i - last_signal_idx < MIN_BARS_BETWEEN:
            continue

        wick_up = WU[i]
        wick_dn = WD[i]
        body = BODY[i]

        max_wick = max(wick_up, wick_dn)
        if max_wick <= body * WICK_MIN_RATIO:
            continue

        if wick_dn > wick_up and wick_dn > body:
            wtype = 'bull_wick'
        elif wick_up > wick_dn and wick_up > body:
            wtype = 'bear_wick'
        else:
            continue

        # Filtro: so bear wicks
        if WICK_ONLY_BEAR and wtype == 'bull_wick':
            continue

        # Filtro EMA20
        if EMA20_FILTER:
            if wtype == 'bull_wick' and C[i] < EMA[i]:
                continue
            if wtype == 'bear_wick' and C[i] > EMA[i]:
                continue

        last_signal_idx = i
        wicks.append({
            'index': i,
            'type': 'wick',
            'wick_type': wtype,
            'bar_rng': H[i] - L[i],
            'high': H[i],
            'low': L[i],
            'wick_ratio': round(max_wick / body, 2) if body > 0 else 99
        })

    return wicks


def calculate_stop(entry_price, bar_high, bar_low, direction):
    """Calcula stop loss"""
    bar_range = bar_high - bar_low
    if bar_range == 0:
        return entry_price

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


def calculate_target(entry_price, stop_loss, direction):
    """Calcula target"""
    risk = abs(entry_price - stop_loss)
    if direction == 'buy':
        return entry_price + risk * RR_RATIO
    else:
        return entry_price - risk * RR_RATIO


def generate_signals(df):
    """Gera sinais com filtros"""
    df = calculate_indicators(df)
    elephants = detect_elephant_bars(df)
    wicks = detect_wick_bars(df)
    patterns = detect_all_patterns(df)
    signals = []

    for e in elephants:
        direction = 'buy' if e['is_bull'] else 'sell'
        entry_price = e['high'] if direction == 'buy' else e['low']
        stop = calculate_stop(entry_price, e['high'], e['low'], direction)

        label = 'E+_' if e['is_plus'] else 'E_'
        label += '1st' if e['is_first'] else '2nd+'
        label += '_Bull' if e['is_bull'] else '_Bear'

        signals.append(Signal(
            signal_type='elephant',
            direction=direction,
            index=e['index'],
            price=entry_price,
            stop=stop,
            bar_range=e['bar_rng'],
            label=label
        ))

    for w in wicks:
        direction = 'buy' if w['wick_type'] == 'bull_wick' else 'sell'
        entry_price = w['high'] if direction == 'buy' else w['low']
        stop = calculate_stop(entry_price, w['high'], w['low'], direction)

        label = 'Wick_Bull' if w['wick_type'] == 'bull_wick' else 'Wick_Bear'

        signals.append(Signal(
            signal_type='wick',
            direction=direction,
            index=w['index'],
            price=entry_price,
            stop=stop,
            bar_range=w['bar_rng'],
            label=label
        ))

    for pat in patterns:
        bar_range = abs(pat['entry'] - pat['stop'])
        signals.append(Signal(
            signal_type='pattern',
            direction=pat['direction'],
            index=pat['index'],
            price=pat['entry'],
            stop=pat['stop'],
            bar_range=bar_range,
            label=pat['label']
        ))

    signals.sort(key=lambda x: x.index)
    return signals


def get_current_signal(df):
    """Verifica sinal na ultima barra"""
    if len(df) < 20:
        return None
    recent = df.iloc[-4:-1]
    signals = generate_signals(recent)
    if signals:
        return signals[-1]
    return None
