"""
RESULTADOS COMPLETOS DO BACKTEST - PATTERNS
Periodo: 60 dias | R:R 1:3 | Stop: 50% bar range
Data: 04/06/2026
"""

# =============================================================================
# RESUMO GERAL - TODOS OS TIMEFRAMES
# =============================================================================

BACKTEST_3m_60d = {
    'BTC/USDT': {
        'trades': 3081, 'per_day': 51, 'wr': 43.6, 'pnl': 262.91, 'pf': 1.43, 'mdd': 26.15,
        'top_patterns': {
            'DESC_TRI': {'trades': 686, 'wr': 56.0, 'pnl': 128.35},
            'DBL_BOT': {'trades': 655, 'wr': 40.6, 'pnl': 29.22},
            'DBL_TOP': {'trades': 654, 'wr': 41.0, 'pnl': 56.01},
        }
    },
    'ETH/USDT': {
        'trades': 2963, 'per_day': 49, 'wr': 43.8, 'pnl': 391.91, 'pf': 1.53, 'mdd': 24.07,
        'top_patterns': {
            'DESC_TRI': {'trades': 673, 'wr': 57.8, 'pnl': 205.14},
            'DBL_BOT': {'trades': 643, 'wr': 37.3, 'pnl': 23.55},
            'DBL_TOP': {'trades': 626, 'wr': 41.4, 'pnl': 81.38},
        }
    }
}

BACKTEST_5m_60d = {
    'BTC/USDT': {
        'trades': 1706, 'per_day': 28, 'wr': 43.6, 'pnl': 166.70, 'pf': 1.38, 'mdd': 27.83,
        'top_patterns': {
            'DESC_TRI': {'trades': 406, 'wr': 58.6, 'pnl': 113.74},
            'DBL_TOP': {'trades': 378, 'wr': 40.2, 'pnl': 22.20},
            'DBL_BOT': {'trades': 344, 'wr': 39.0, 'pnl': 13.94},
        }
    },
    'ETH/USDT': {
        'trades': 3052, 'per_day': 51, 'wr': 44.5, 'pnl': 382.88, 'pf': 1.37, 'mdd': 60.05,
        'top_patterns': {
            'DESC_TRI': {'trades': 414, 'wr': 46.9, 'pnl': 68.36},
            'ASC_TRI': {'trades': 402, 'wr': 42.3, 'pnl': 15.59},
            'RISE_WEDGE': {'trades': 377, 'wr': 53.3, 'pnl': 101.50},
        }
    }
}

BACKTEST_15m_60d = {
    'BTC/USDT': {
        'trades': 883, 'per_day': 15, 'wr': 46.5, 'pnl': 330.88, 'pf': 1.85, 'mdd': 38.55,
        'top_patterns': {
            'RISE_WEDGE': {'trades': 126, 'wr': 46.8, 'pnl': 97.45},
            'ASC_TRI': {'trades': 123, 'wr': 48.8, 'pnl': 28.92},
            'DBL_TOP': {'trades': 124, 'wr': 38.7, 'pnl': 18.15},
        }
    },
    'ETH/USDT': {
        'trades': 555, 'per_day': 9, 'wr': 42.9, 'pnl': 127.19, 'pf': 1.38, 'mdd': 27.97,
        'top_patterns': {
            'DESC_TRI': {'trades': 125, 'wr': 53.6, 'pnl': 45.95},
            'DBL_TOP': {'trades': 120, 'wr': 40.8, 'pnl': 35.68},
            'TRI_TOP': {'trades': 82, 'wr': 46.3, 'pnl': 34.14},
        }
    }
}

BACKTEST_30m_60d = {
    'BTC/USDT': {
        'trades': 483, 'per_day': 8, 'wr': 44.1, 'pnl': 121.61, 'pf': 1.37, 'mdd': 52.47,
        'top_patterns': {
            'RISE_WEDGE': {'trades': 73, 'wr': 60.3, 'pnl': 53.75},
            'ASC_TRI': {'trades': 61, 'wr': 50.8, 'pnl': 22.23},
            'SYM_TRI_BEAR': {'trades': 40, 'wr': 57.5, 'pnl': 23.29},
        }
    },
    'ETH/USDT': {
        'trades': 293, 'per_day': 5, 'wr': 45.4, 'pnl': 83.00, 'pf': 1.37, 'mdd': 30.73,
        'top_patterns': {
            'DBL_TOP': {'trades': 65, 'wr': 43.1, 'pnl': 31.38},
            'TRI_TOP': {'trades': 47, 'wr': 55.3, 'pnl': 31.42},
            'H&S': {'trades': 13, 'wr': 69.2, 'pnl': 13.59},
        }
    }
}

BACKTEST_1h_60d = {
    'BTC/USDT': {
        'trades': 227, 'per_day': 4, 'wr': 41.0, 'pnl': -35.94, 'pf': 0.84, 'mdd': 55.40,
        'status': 'PERDENDO - NAO USAR'
    },
    'ETH/USDT': {
        'trades': 186, 'per_day': 3, 'wr': 50.0, 'pnl': 66.79, 'pf': 1.40, 'mdd': 41.76,
        'top_patterns': {
            'TRI_TOP': {'trades': 16, 'wr': 68.8, 'pnl': 23.28},
            'DBL_TOP': {'trades': 20, 'wr': 55.0, 'pnl': 21.88},
            'RISE_WEDGE': {'trades': 29, 'wr': 62.1, 'pnl': 11.86},
        }
    }
}

# =============================================================================
# RANKING GERAL (ordenado por PnL)
# =============================================================================

RANKING = [
    {'par': 'ETH/USDT', 'tf': '3m', 'per_day': 49, 'wr': 43.8, 'pnl': 391.91, 'pf': 1.53, 'mdd': 24.07},
    {'par': 'ETH/USDT', 'tf': '5m', 'per_day': 51, 'wr': 44.5, 'pnl': 382.88, 'pf': 1.37, 'mdd': 60.05},
    {'par': 'BTC/USDT', 'tf': '3m', 'per_day': 51, 'wr': 43.6, 'pnl': 262.91, 'pf': 1.43, 'mdd': 26.15},
    {'par': 'BTC/USDT', 'tf': '15m', 'per_day': 15, 'wr': 46.5, 'pnl': 330.88, 'pf': 1.85, 'mdd': 38.55},
    {'par': 'ETH/USDT', 'tf': '15m', 'per_day': 9, 'wr': 42.9, 'pnl': 127.19, 'pf': 1.38, 'mdd': 27.97},
    {'par': 'BTC/USDT', 'tf': '5m', 'per_day': 28, 'wr': 43.6, 'pnl': 166.70, 'pf': 1.38, 'mdd': 27.83},
    {'par': 'BTC/USDT', 'tf': '30m', 'per_day': 8, 'wr': 44.1, 'pnl': 121.61, 'pf': 1.37, 'mdd': 52.47},
    {'par': 'ETH/USDT', 'tf': '30m', 'per_day': 5, 'wr': 45.4, 'pnl': 83.00, 'pf': 1.37, 'mdd': 30.73},
    {'par': 'ETH/USDT', 'tf': '1h', 'per_day': 3, 'wr': 50.0, 'pnl': 66.79, 'pf': 1.40, 'mdd': 41.76},
    {'par': 'BTC/USDT', 'tf': '1h', 'per_day': 4, 'wr': 41.0, 'pnl': -35.94, 'pf': 0.84, 'mdd': 55.40},
]

# =============================================================================
# FILTROS TESTADOS (60 dias)
# =============================================================================

FILTROS_30m = {
    'BTC/USDT': {
        'baseline': {'trades_per_day': 3, 'wr': 43.3, 'pnl': 32.75, 'pf': 1.26, 'mdd': 23.17},
        'bull_body': {'trades_per_day': 1, 'wr': 42.6, 'pnl': 19.26, 'pf': 1.45, 'mdd': 12.33},
        'bear_body': {'trades_per_day': 1, 'wr': 39.2, 'pnl': -8.52, 'pf': 0.88, 'mdd': 40.45},
    },
    'ETH/USDT': {
        'baseline': {'trades_per_day': 2, 'wr': 40.8, 'pnl': 10.34, 'pf': 1.09, 'mdd': 22.09},
        'bear_body': {'trades_per_day': 1, 'wr': 47.5, 'pnl': 22.00, 'pf': 1.49, 'mdd': 16.28},
    }
}

FILTROS_15m = {
    'BTC/USDT': {
        'baseline': {'trades_per_day': 5, 'wr': 47.8, 'pnl': 128.25, 'pf': 1.99, 'mdd': 11.93},
        'bear': {'trades_per_day': 3, 'wr': 44.6, 'pnl': 88.05, 'pf': 2.16, 'mdd': 27.52},
        'bull_body': {'trades_per_day': 2, 'wr': 51.6, 'pnl': 40.84, 'pf': 1.91, 'mdd': 6.96},
    },
    'ETH/USDT': {
        'baseline': {'trades_per_day': 5, 'wr': 41.5, 'pnl': 34.99, 'pf': 1.21, 'mdd': 20.53},
        'bear_body': {'trades_per_day': 2, 'wr': 45.7, 'pnl': 36.15, 'pf': 1.48, 'mdd': 17.71},
    }
}

# =============================================================================
# CONCLUSOES
# =============================================================================

CONCLUSOES = """
============================================================
  CONCLUSÕES DO BACKTEST - PATTERNS (60 dias)
============================================================

  TOP 3 MELHORES COMBOS:
  1. ETH/USDT 3m: +392%, PF 1.53, 49 trades/dia, MDD 24%
  2. ETH/USDT 5m: +383%, PF 1.37, 51 trades/dia, MDD 60%
  3. BTC/USDT 15m: +331%, PF 1.85, 15 trades/dia, MDD 39%

  TOP 3 MENOR RISCO (MDD):
  1. BTC/USDT 15m bull+body: MDD 7%, PF 1.91
  2. BTC/USDT 15m baseline: MDD 12%, PF 1.99
  3. ETH/USDT 3m: MDD 24%, PF 1.53

  PADRÕES MAIS LUCRATIVOS:
  - DESC_TRI (Descending Triangle): WR 56-58%, forte no 3m/5m
  - RISE_WEDGE: forte no 15m/30m
  - ASC_TRI: forte no 3m
  - DBL_TOP/BOT: frequentes mas WR menor

  PADRÕES PERDEDORES:
  - INV_H&S no 5m: perde dinheiro
  - BTC 1h: nao usar (PF 0.84)

  FILTROS QUE FUNCIONAM:
  - So Bear + Body>50%: reduz trades, melhora PF
  - So Bull + Body>50%: MDD baixo no BTC 15m

============================================================
"""
