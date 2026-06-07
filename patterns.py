"""
20 PADROES COMPLEXOS DE ANALISE TECNICA
Baseado na aula completa de padroes complexos.

Cada funcao retorna lista de sinais com:
  - index: onde o padrao termina
  - type: nome do padrao
  - direction: 'buy' ou 'sell'
  - entry: preco de entrada
  - stop: stop loss
  - label: descricao
"""
import numpy as np
from config import *


def _find_swing_highs(lows, highs, order=5):
    """Encontra topos (pivots altos)"""
    tops = []
    for i in range(order, len(highs) - order):
        if all(highs[i] >= highs[i-j] for j in range(1, order+1)) and \
           all(highs[i] >= highs[i+j] for j in range(1, order+1)):
            tops.append(i)
    return tops

def _find_swing_lows(lows, highs, order=5):
    """Encontra fundos (pivots baixos)"""
    bottoms = []
    for i in range(order, len(lows) - order):
        if all(lows[i] <= lows[i-j] for j in range(1, order+1)) and \
           all(lows[i] <= lows[i+j] for j in range(1, order+1)):
            bottoms.append(i)
    return bottoms

def _bar_size(df, i):
    return df['h'].values[i] - df['l'].values[i]

def _is_green(df, i):
    return df['c'].values[i] > df['o'].values[i]

def _is_red(df, i):
    return df['c'].values[i] < df['o'].values[i]

def _body_size(df, i):
    return abs(df['c'].values[i] - df['o'].values[i])


# ============================================================
# 1. OMBRO CABECA OMBRO (Reversao de alta para baixa)
# ============================================================
def detect_head_shoulders(df):
    """Ombro Cabeca Ombro: 2 fundos no mesmo nivel, 3 topos (central mais alto)"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    O = df['o'].values

    tops = _find_swing_highs(L, H, order=5)
    bottoms = _find_swing_lows(L, H, order=5)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2, t3 = tops[i], tops[i+1], tops[i+2]

        # T2 (cabeca) deve ser mais alto que T1 e T3
        if H[t2] <= H[t1] or H[t2] <= H[t3]:
            continue

        # T1 e T3 devem ser proximos (ombros)
        shoulder_diff = abs(H[t1] - H[t3]) / H[t2]
        if shoulder_diff > 0.03:  # 3% tolerancia
            continue

        # Encontrar fundos entre os topos
        bottoms_between = [b for b in bottoms if t1 < b < t3]
        if len(bottoms_between) < 2:
            continue

        # Linha de pescoco: suporte dos fundos
        neckline = min(L[bottoms_between])

        # Rompimento: candle fechado abaixo do pescoco
        for j in range(t3 + 1, min(t3 + 20, n)):
            if C[j] < neckline:
                entry = neckline
                stop = H[t2]
                risk = stop - entry
                target = entry - risk * RR_RATIO

                signals.append({
                    'index': j,
                    'type': 'head_shoulders',
                    'direction': 'sell',
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'label': 'H&S',
                    'neckline': neckline
                })
                break

    return signals


# ============================================================
# 2. OMBRO CABECA OMBRO INVERTIDO (Reversao de baixa para alta)
# ============================================================
def detect_inv_head_shoulders(df):
    """Ombro Cabeca Ombro Invertido: 3 fundos (central mais baixo), 2 topos no mesmo nivel"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values

    tops = _find_swing_highs(L, H, order=5)
    bottoms = _find_swing_lows(L, H, order=5)
    signals = []

    for i in range(len(bottoms) - 2):
        b1, b2, b3 = bottoms[i], bottoms[i+1], bottoms[i+2]

        if L[b2] >= L[b1] or L[b2] >= L[b3]:
            continue

        shoulder_diff = abs(L[b1] - L[b3]) / L[b2]
        if shoulder_diff > 0.03:
            continue

        tops_between = [t for t in tops if b1 < t < b3]
        if len(tops_between) < 2:
            continue

        neckline = max(H[tops_between])

        for j in range(b3 + 1, min(b3 + 20, n)):
            if C[j] > neckline:
                entry = neckline
                stop = L[b2]
                risk = entry - stop
                target = entry + risk * RR_RATIO

                signals.append({
                    'index': j,
                    'type': 'inv_head_shoulders',
                    'direction': 'buy',
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'label': 'INV_H&S',
                    'neckline': neckline
                })
                break

    return signals


# ============================================================
# 3. FUNDO DUPLO
# ============================================================
def detect_double_bottom(df):
    """Fundo Duplo: 2 fundos no mesmo nivel, rompe topo"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    bottoms = _find_swing_lows(L, H, order=5)
    tops = _find_swing_highs(L, H, order=5)
    signals = []

    for i in range(len(bottoms) - 1):
        b1, b2 = bottoms[i], bottoms[i+1]

        # Fundos proximos
        diff = abs(L[b1] - L[b2]) / L[b1]
        if diff > 0.02:  # 2% tolerancia
            continue

        # Topo entre os fundos
        tops_between = [t for t in tops if b1 < t < b2]
        if not tops_between:
            continue

        resistance = max(H[tops_between])

        for j in range(b2 + 1, min(b2 + 20, n)):
            if C[j] > resistance:
                entry = resistance
                stop = min(L[b1], L[b2])
                risk = entry - stop
                target = entry + risk * RR_RATIO

                signals.append({
                    'index': j,
                    'type': 'double_bottom',
                    'direction': 'buy',
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'label': 'DBL_BOT'
                })
                break

    return signals


# ============================================================
# 4. TOPO DUPLO
# ============================================================
def detect_double_top(df):
    """Topo Duplo: 2 topos no mesmo nivel, rompe fundo"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=5)
    bottoms = _find_swing_lows(L, H, order=5)
    signals = []

    for i in range(len(tops) - 1):
        t1, t2 = tops[i], tops[i+1]

        diff = abs(H[t1] - H[t2]) / H[t1]
        if diff > 0.02:
            continue

        bottoms_between = [b for b in bottoms if t1 < b < t2]
        if not bottoms_between:
            continue

        support = min(L[bottoms_between])

        for j in range(t2 + 1, min(t2 + 20, n)):
            if C[j] < support:
                entry = support
                stop = max(H[t1], H[t2])
                risk = stop - entry
                target = entry - risk * RR_RATIO

                signals.append({
                    'index': j,
                    'type': 'double_top',
                    'direction': 'sell',
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'label': 'DBL_TOP'
                })
                break

    return signals


# ============================================================
# 5. FUNDO TRIPLO
# ============================================================
def detect_triple_bottom(df):
    """Fundo Triplo: 3 fundos, 2 topos, rompe topos"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    bottoms = _find_swing_lows(L, H, order=5)
    tops = _find_swing_highs(L, H, order=5)
    signals = []

    for i in range(len(bottoms) - 2):
        b1, b2, b3 = bottoms[i], bottoms[i+1], bottoms[i+2]

        # Fundos proximos
        avg_low = (L[b1] + L[b2] + L[b3]) / 3
        for b in [b1, b2, b3]:
            if abs(L[b] - avg_low) / avg_low > 0.03:
                break
        else:
            tops_between = [t for t in tops if b1 < t < b3]
            if len(tops_between) < 2:
                continue

            resistance = max(H[tops_between])

            for j in range(b3 + 1, min(b3 + 20, n)):
                if C[j] > resistance:
                    entry = resistance
                    stop = avg_low
                    risk = entry - stop
                    target = entry + risk * RR_RATIO

                    signals.append({
                        'index': j,
                        'type': 'triple_bottom',
                        'direction': 'buy',
                        'entry': entry,
                        'stop': stop,
                        'target': target,
                        'label': 'TRI_BOT'
                    })
                    break

    return signals


# ============================================================
# 6. TOPO TRIPLO
# ============================================================
def detect_triple_top(df):
    """Topo Triplo: 3 topos, 2 fundos, rompe fundos"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=5)
    bottoms = _find_swing_lows(L, H, order=5)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2, t3 = tops[i], tops[i+1], tops[i+2]

        avg_high = (H[t1] + H[t2] + H[t3]) / 3
        for t in [t1, t2, t3]:
            if abs(H[t] - avg_high) / avg_high > 0.03:
                break
        else:
            bottoms_between = [b for b in bottoms if t1 < b < t3]
            if len(bottoms_between) < 2:
                continue

            support = min(L[bottoms_between])

            for j in range(t3 + 1, min(t3 + 20, n)):
                if C[j] < support:
                    entry = support
                    stop = avg_high
                    risk = stop - entry
                    target = entry - risk * RR_RATIO

                    signals.append({
                        'index': j,
                        'type': 'triple_top',
                        'direction': 'sell',
                        'entry': entry,
                        'stop': stop,
                        'target': target,
                        'label': 'TRI_TOP'
                    })
                    break

    return signals


# ============================================================
# 7. CUNHA DESCENDENTE (Alta)
# ============================================================
def detect_falling_wedge(df):
    """Cunha Descendente: topos e fundos descendentes, rompe para cima"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2 = tops[i], tops[i+1]
        b1, b2 = bottoms[i], bottoms[i+1]

        if t2 >= t1 or b2 >= b1:  # Descendente
            continue
        if b2 <= b1 and t2 <= t1:
            # Verificar convergencia
            t_slope = (H[t2] - H[t1]) / (t2 - t1)
            b_slope = (L[b2] - L[b1]) / (b2 - b1)
            if t_slope < b_slope:  # Convergente
                resistance = H[t2]
                for j in range(t2 + 1, min(t2 + 30, n)):
                    if C[j] > resistance:
                        entry = resistance
                        stop = L[b2]
                        risk = entry - stop
                        target = entry + risk * RR_RATIO
                        signals.append({
                            'index': j, 'type': 'falling_wedge',
                            'direction': 'buy', 'entry': entry,
                            'stop': stop, 'target': target,
                            'label': 'FALL_WEDGE'
                        })
                        break

    return signals


# ============================================================
# 8. CUNHA ASCENDENTE (Baixa)
# ============================================================
def detect_rising_wedge(df):
    """Cunha Ascendente: topos e fundos ascendentes, rompe para baixo"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2 = tops[i], tops[i+1]
        b1, b2 = bottoms[i], bottoms[i+1]

        if t2 <= t1 or b2 <= b1:  # Ascendente
            continue
        if b2 >= b1 and t2 >= t1:
            t_slope = (H[t2] - H[t1]) / (t2 - t1)
            b_slope = (L[b2] - L[b1]) / (b2 - b1)
            if b_slope > t_slope:  # Convergente
                support = L[b2]
                for j in range(b2 + 1, min(b2 + 30, n)):
                    if C[j] < support:
                        entry = support
                        stop = H[t2]
                        risk = stop - entry
                        target = entry - risk * RR_RATIO
                        signals.append({
                            'index': j, 'type': 'rising_wedge',
                            'direction': 'sell', 'entry': entry,
                            'stop': stop, 'target': target,
                            'label': 'RISE_WEDGE'
                        })
                        break

    return signals


# ============================================================
# 9. ALARGAMENTO ALTISTA (Megaphone Top)
# ============================================================
def detect_broadening_top(df):
    """Alargamento: topos mais altos, fundos mais baixos"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2 = tops[i], tops[i+1]
        b1, b2 = bottoms[i], bottoms[i+1]

        # Topos mais altos, fundos mais baixos
        if H[t2] > H[t1] and L[b2] < L[b1]:
            # Rompe ultimo fundo = venda
            for j in range(b2 + 1, min(b2 + 20, n)):
                if C[j] < L[b2]:
                    entry = L[b2]
                    stop = H[t2]
                    risk = stop - entry
                    target = entry - risk * RR_RATIO
                    signals.append({
                        'index': j, 'type': 'broadening_top',
                        'direction': 'sell', 'entry': entry,
                        'stop': stop, 'target': target,
                        'label': 'BROAD_TOP'
                    })
                    break

    return signals


# ============================================================
# 10. ALARGAMENTO BAIXISTA
# ============================================================
def detect_broadening_bottom(df):
    """Alargamento Baixista: rompe ultimo topo"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2 = tops[i], tops[i+1]
        b1, b2 = bottoms[i], bottoms[i+1]

        if H[t2] > H[t1] and L[b2] < L[b1]:
            for j in range(t2 + 1, min(t2 + 20, n)):
                if C[j] > H[t2]:
                    entry = H[t2]
                    stop = L[b2]
                    risk = entry - stop
                    target = entry + risk * RR_RATIO
                    signals.append({
                        'index': j, 'type': 'broadening_bottom',
                        'direction': 'buy', 'entry': entry,
                        'stop': stop, 'target': target,
                        'label': 'BROAD_BOT'
                    })
                    break

    return signals


# ============================================================
# 11. RETANGULO ALTISTA
# ============================================================
def detect_bull_rectangle(df):
    """Retangulo: consolidacao lateral, rompe para cima"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values

    for lookback in [20, 30, 40]:
        for i in range(lookback + 10, n):
            window = range(i - lookback, i)
            highs_w = H[window]
            lows_w = L[window]

            resistance = np.percentile(highs_w, 90)
            support = np.percentile(lows_w, 10)

            # Range lateral
            rng = resistance - support
            if rng / resistance > 0.05:  # Range > 5%
                continue

            # Topos e fundos no range
            touches_r = sum(1 for h in highs_w if abs(h - resistance) / resistance < 0.01)
            touches_s = sum(1 for l in lows_w if abs(l - support) / support < 0.01)

            if touches_r >= 2 and touches_s >= 2:
                # Rompe resistencia
                if i < n and C[i] > resistance:
                    entry = resistance
                    stop = support
                    risk = entry - stop
                    target = entry + risk * RR_RATIO
                    return [{'index': i, 'type': 'bull_rectangle',
                             'direction': 'buy', 'entry': entry,
                             'stop': stop, 'target': target,
                             'label': 'BULL_RECT'}]

    return []


# ============================================================
# 12. RETANGULO BAIXISTA
# ============================================================
def detect_bear_rectangle(df):
    """Retangulo: consolidacao lateral, rompe para baixo"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values

    for lookback in [20, 30, 40]:
        for i in range(lookback + 10, n):
            window = range(i - lookback, i)
            highs_w = H[window]
            lows_w = L[window]

            resistance = np.percentile(highs_w, 90)
            support = np.percentile(lows_w, 10)

            rng = resistance - support
            if rng / resistance > 0.05:
                continue

            touches_r = sum(1 for h in highs_w if abs(h - resistance) / resistance < 0.01)
            touches_s = sum(1 for l in lows_w if abs(l - support) / support < 0.01)

            if touches_r >= 2 and touches_s >= 2:
                if i < n and C[i] < support:
                    entry = support
                    stop = resistance
                    risk = stop - entry
                    target = entry - risk * RR_RATIO
                    return [{'index': i, 'type': 'bear_rectangle',
                             'direction': 'sell', 'entry': entry,
                             'stop': stop, 'target': target,
                             'label': 'BEAR_RECT'}]

    return []


# ============================================================
# 13. BANDEIRA ALTISTA (Mastro + correcao <= 1/3)
# ============================================================
def detect_bull_flag(df):
    """Bandeira Altista: movimento forte + correcao curta"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    O = df['o'].values

    for i in range(30, n - 10):
        # Procurar mastro: 3+ barras verdes fortes
        mastro_start = None
        for j in range(i, max(i-15, 0), -1):
            if _is_green(df, j) and _bar_size(df, j) > 0:
                if mastro_start is None:
                    mastro_start = j
                elif _is_green(df, j):
                    mastro_start = j
                else:
                    break

        if mastro_start is None:
            continue

        mastro_low = L[mastro_start]
        mastro_high = H[i]
        mastro_range = mastro_high - mastro_low

        if mastro_range <= 0:
            continue

        # Bandeira: correcao max 1/3 do mastro
        flag_high = H[i]
        flag_low = min(L[i-5:i+1]) if i >= 5 else L[i]
        flag_range = flag_high - flag_low

        if flag_range > mastro_range / 3:
            continue

        # Rompe topos da bandeira
        resistance = max(H[i-3:i+1]) if i >= 3 else H[i]
        if C[i] > resistance:
            entry = resistance
            stop = flag_low
            risk = entry - stop
            target = entry + mastro_range  # Alvo = amplitude do mastro
            return [{'index': i, 'type': 'bull_flag',
                     'direction': 'buy', 'entry': entry,
                     'stop': stop, 'target': target,
                     'label': 'BULL_FLAG'}]

    return []


# ============================================================
# 14. BANDEIRA BAIXISTA
# ============================================================
def detect_bear_flag(df):
    """Bandeira Baixista: queda forte + repique curto"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values

    for i in range(30, n - 10):
        mastro_start = None
        for j in range(i, max(i-15, 0), -1):
            if _is_red(df, j) and _bar_size(df, j) > 0:
                if mastro_start is None:
                    mastro_start = j
                elif _is_red(df, j):
                    mastro_start = j
                else:
                    break

        if mastro_start is None:
            continue

        mastro_high = H[mastro_start]
        mastro_low = L[i]
        mastro_range = mastro_high - mastro_low

        if mastro_range <= 0:
            continue

        flag_high = max(H[i-5:i+1]) if i >= 5 else H[i]
        flag_low = L[i]
        flag_range = flag_high - flag_low

        if flag_range > mastro_range / 3:
            continue

        support = min(L[i-3:i+1]) if i >= 3 else L[i]
        if C[i] < support:
            entry = support
            stop = flag_high
            risk = stop - entry
            target = entry - mastro_range
            return [{'index': i, 'type': 'bear_flag',
                     'direction': 'sell', 'entry': entry,
                     'stop': stop, 'target': target,
                     'label': 'BEAR_FLAG'}]

    return []


# ============================================================
# 15. TRIANGULO SIMETRICO ALTISTA
# ============================================================
def detect_sym_triangle_bull(df):
    """Triangulo Simetrico: topos baixos, fundos altos, rompe cima"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2 = tops[i], tops[i+1]
        b1, b2 = bottoms[i], bottoms[i+1]

        # Topos mais baixos, fundos mais altos
        if H[t2] < H[t1] and L[b2] > L[b1]:
            resistance = H[t2]
            for j in range(t2 + 1, min(t2 + 30, n)):
                if C[j] > resistance:
                    entry = resistance
                    stop = L[b2]
                    risk = entry - stop
                    target = entry + risk * RR_RATIO
                    signals.append({
                        'index': j, 'type': 'sym_triangle_bull',
                        'direction': 'buy', 'entry': entry,
                        'stop': stop, 'target': target,
                        'label': 'SYM_TRI_BULL'
                    })
                    break

    return signals


# ============================================================
# 16. TRIANGULO SIMETRICO BAIXISTA
# ============================================================
def detect_sym_triangle_bear(df):
    """Triangulo Simetrico: rompe fundo"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2 = tops[i], tops[i+1]
        b1, b2 = bottoms[i], bottoms[i+1]

        if H[t2] < H[t1] and L[b2] > L[b1]:
            support = L[b2]
            for j in range(b2 + 1, min(b2 + 30, n)):
                if C[j] < support:
                    entry = support
                    stop = H[t2]
                    risk = stop - entry
                    target = entry - risk * RR_RATIO
                    signals.append({
                        'index': j, 'type': 'sym_triangle_bear',
                        'direction': 'sell', 'entry': entry,
                        'stop': stop, 'target': target,
                        'label': 'SYM_TRI_BEAR'
                    })
                    break

    return signals


# ============================================================
# 17. TRIANGULO ASCENDENTE
# ============================================================
def detect_ascending_triangle(df):
    """Triangulo Ascendente: topos no mesmo nivel, fundos altos"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(tops) - 2):
        t1, t2 = tops[i], tops[i+1]
        b1, b2 = bottoms[i], bottoms[i+1]

        # Topos proximos, fundos subindo
        if abs(H[t1] - H[t2]) / H[t1] < 0.02 and L[b2] > L[b1]:
            resistance = H[t1]
            for j in range(t2 + 1, min(t2 + 30, n)):
                if C[j] > resistance:
                    entry = resistance
                    stop = L[b2]
                    risk = entry - stop
                    target = entry + risk * RR_RATIO
                    signals.append({
                        'index': j, 'type': 'ascending_triangle',
                        'direction': 'buy', 'entry': entry,
                        'stop': stop, 'target': target,
                        'label': 'ASC_TRI'
                    })
                    break

    return signals


# ============================================================
# 18. TRIANGULO DESCENDENTE
# ============================================================
def detect_descending_triangle(df):
    """Triangulo Descendente: fundos no mesmo nivel, topos baixos"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=4)
    bottoms = _find_swing_lows(L, H, order=4)
    signals = []

    for i in range(len(bottoms) - 2):
        b1, b2 = bottoms[i], bottoms[i+1]
        t1, t2 = tops[i], tops[i+1]

        if abs(L[b1] - L[b2]) / L[b1] < 0.02 and H[t2] < H[t1]:
            support = L[b1]
            for j in range(b2 + 1, min(b2 + 30, n)):
                if C[j] < support:
                    entry = support
                    stop = H[t2]
                    risk = stop - entry
                    target = entry - risk * RR_RATIO
                    signals.append({
                        'index': j, 'type': 'descending_triangle',
                        'direction': 'sell', 'entry': entry,
                        'stop': stop, 'target': target,
                        'label': 'DESC_TRI'
                    })
                    break

    return signals


# ============================================================
# 19. CUP AND HANDLE (Xicara)
# ============================================================
def detect_cup_handle(df):
    """Cup and Handle: fundos arredondados, 2o fundo = metade do 1o"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    bottoms = _find_swing_lows(L, H, order=5)
    signals = []

    for i in range(len(bottoms) - 1):
        b1, b2 = bottoms[i], bottoms[i+1]

        # Segundo fundo menor
        if L[b2] >= L[b1]:
            continue

        # Distancia entre fundos minima
        if b2 - b1 < 10:
            continue

        # Topo entre fundos (borda da xicara)
        cup_edge = max(H[b1:b2+1])
        cup_depth = cup_edge - L[b1]

        # Handle: correcao curta apos b2
        handle_end = min(b2 + 10, n - 1)
        handle_low = min(L[b2:handle_end+1])
        handle_range = cup_edge - handle_low

        # Handle deve ser < 1/3 do copo
        if handle_range > cup_depth / 3:
            continue

        # Rompe borda da xicara
        for j in range(handle_end + 1, min(handle_end + 15, n)):
            if C[j] > cup_edge:
                entry = cup_edge
                stop = handle_low
                risk = entry - stop
                target = entry + cup_depth
                signals.append({
                    'index': j, 'type': 'cup_handle',
                    'direction': 'buy', 'entry': entry,
                    'stop': stop, 'target': target,
                    'label': 'CUP_HANDLE'
                })
                break

    return signals


# ============================================================
# 20. CUP AND HANDLE INVERTIDO
# ============================================================
def detect_inv_cup_handle(df):
    """Cup and Handle Invertido: topos arredondados, rompe para baixo"""
    n = len(df)
    H = df['h'].values; L = df['l'].values; C = df['c'].values
    tops = _find_swing_highs(L, H, order=5)
    signals = []

    for i in range(len(tops) - 1):
        t1, t2 = tops[i], tops[i+1]

        if H[t2] <= H[t1]:
            continue

        if t2 - t1 < 10:
            continue

        cup_floor = min(L[t1:t2+1])
        cup_depth = H[t1] - cup_floor

        handle_end = min(t2 + 10, n - 1)
        handle_high = max(H[t2:handle_end+1])
        handle_range = handle_high - cup_floor

        if handle_range > cup_depth / 3:
            continue

        for j in range(handle_end + 1, min(handle_end + 15, n)):
            if C[j] < cup_floor:
                entry = cup_floor
                stop = handle_high
                risk = stop - entry
                target = entry - cup_depth
                signals.append({
                    'index': j, 'type': 'inv_cup_handle',
                    'direction': 'sell', 'entry': entry,
                    'stop': stop, 'target': target,
                    'label': 'INV_CUP'
                })
                break

    return signals


# ============================================================
# FUNCAO PRINCIPAL: DETECTAR TODOS OS PADROES
# ============================================================
def detect_all_patterns(df):
    """Detecta todos os 20 padroes complexos"""
    all_signals = []

    detectors = [
        detect_head_shoulders,
        detect_inv_head_shoulders,
        detect_double_bottom,
        detect_double_top,
        detect_triple_bottom,
        detect_triple_top,
        detect_falling_wedge,
        detect_rising_wedge,
        detect_broadening_top,
        detect_broadening_bottom,
        detect_bull_rectangle,
        detect_bear_rectangle,
        detect_bull_flag,
        detect_bear_flag,
        detect_sym_triangle_bull,
        detect_sym_triangle_bear,
        detect_ascending_triangle,
        detect_descending_triangle,
        detect_cup_handle,
        detect_inv_cup_handle,
    ]

    for detector in detectors:
        try:
            signals = detector(df)
            all_signals.extend(signals)
        except:
            pass

    all_signals.sort(key=lambda x: x['index'])
    return all_signals
