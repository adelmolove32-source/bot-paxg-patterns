import numpy as np
import pandas as pd
from config_paxg import *
from patterns import detect_all_patterns


class Signal:
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
    df = df.copy()
    df['body'] = abs(df['c'] - df['o'])
    df['rng'] = (df['h'] - df['l']).replace(0, np.nan)
    df['avg_rng'] = df['rng'].rolling(10).mean()
    df['ema20'] = df['c'].ewm(span=20, adjust=False).mean()
    return df


def generate_signals(df):
    df = calculate_indicators(df)
    patterns = detect_all_patterns(df)
    signals = []

    for pat in patterns:
        if pat['label'] not in ENABLED_PATTERNS:
            continue

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
    if len(df) < 20:
        return None
    recent = df.iloc[-4:-1]
    signals = generate_signals(recent)
    if signals:
        return signals[-1]
    return None
