"""
RESULTADO COMPLETO - BACKTEST REALISTA
Max 3 posicoes simultaneas | 50% cada | R:R 1:3 | 60 dias | Banca $200
Data: 05/06/2026
"""

# =============================================================================
# RANKING GERAL - TODOS OS TIMEFRAMES
# =============================================================================
RANKING_GERAL = [
    {"#": 1, "par": "ETH/USDT", "tf": "3m", "trades_dia": 18.4, "wr": 45.8, "pnl": 164.6, "pf": 1.73, "mdd": 6.6, "saldo": 529},
    {"#": 2, "par": "ETH/USDT", "tf": "5m", "trades_dia": 13.7, "wr": 49.1, "pnl": 137.6, "pf": 1.68, "mdd": 16.3, "saldo": 475},
    {"#": 3, "par": "BTC/USDT", "tf": "3m", "trades_dia": 19.4, "wr": 47.3, "pnl": 118.3, "pf": 1.68, "mdd": 5.3, "saldo": 437},
    {"#": 4, "par": "BTC/USDT", "tf": "5m", "trades_dia": 11.0, "wr": 46.1, "pnl": 67.1, "pf": 1.61, "mdd": 5.9, "saldo": 334},
    {"#": 5, "par": "ETH/USDT", "tf": "15m", "trades_dia": 3.8, "wr": 45.6, "pnl": 48.1, "pf": 1.67, "mdd": 8.5, "saldo": 296},
    {"#": 6, "par": "ETH/USDT", "tf": "30m", "trades_dia": 1.9, "wr": 51.3, "pnl": 47.7, "pf": 2.05, "mdd": 8.4, "saldo": 295},
    {"#": 7, "par": "BTC/USDT", "tf": "15m", "trades_dia": 4.6, "wr": 44.4, "pnl": 32.2, "pf": 1.51, "mdd": 16.4, "saldo": 265},
    {"#": 8, "par": "BTC/USDT", "tf": "30m", "trades_dia": 2.6, "wr": 37.6, "pnl": 23.6, "pf": 1.45, "mdd": 16.6, "saldo": 247},
    {"#": 9, "par": "BTC/USDT", "tf": "1h", "trades_dia": 1.1, "wr": 47.8, "pnl": 12.1, "pf": 1.48, "mdd": 4.5, "saldo": 224},
    {"#": 10, "par": "ETH/USDT", "tf": "1h", "trades_dia": 1.3, "wr": 46.8, "pnl": 11.6, "pf": 1.36, "mdd": 16.0, "saldo": 223},
]

# =============================================================================
# TOP PATTERNS POR TIMEFRAME
# =============================================================================
TOP_PATTERNS = {
    "ETH/USDT 3m": [
        ("DESC_TRI", 231, 60.2, 155),
        ("DBL_TOP", 303, 45.9, 123),
        ("H&S", 61, 42.6, 21),
        ("TRI_BOT", 76, 46.1, 19),
        ("TRI_TOP", 69, 42.0, 14),
    ],
    "ETH/USDT 5m": [
        ("DBL_TOP", 160, 51.2, 89),
        ("SYM_TRI_BULL", 68, 61.8, 46),
        ("ASC_TRI", 92, 56.5, 41),
        ("TRI_TOP", 45, 55.6, 39),
        ("H&S", 40, 50.0, 33),
    ],
    "BTC/USDT 3m": [
        ("DESC_TRI", 242, 59.5, 88),
        ("DBL_TOP", 316, 47.5, 82),
        ("TRI_TOP", 70, 45.7, 21),
        ("DBL_BOT", 325, 43.4, 21),
        ("H&S", 72, 36.1, 13),
    ],
    "BTC/USDT 5m": [
        ("DESC_TRI", 148, 58.1, 67),
        ("DBL_TOP", 122, 44.3, 27),
        ("RISE_WEDGE", 66, 48.5, 22),
        ("TRI_TOP", 34, 47.1, 14),
        ("ASC_TRI", 38, 42.1, 10),
    ],
    "ETH/USDT 15m": [
        ("DBL_TOP", 36, 44.4, 36),
        ("TRI_TOP", 24, 54.2, 21),
        ("DESC_TRI", 34, 52.9, 19),
        ("H&S", 10, 60.0, 10),
        ("TRI_BOT", 20, 40.0, 3),
    ],
    "ETH/USDT 30m": [
        ("DBL_TOP", 34, 58.8, 46),
        ("H&S", 6, 83.3, 21),
        ("TRI_TOP", 14, 64.3, 21),
        ("DESC_TRI", 17, 41.2, 14),
        ("TRI_BOT", 9, 55.6, 6),
    ],
    "BTC/USDT 15m": [
        ("TRI_TOP", 30, 53.3, 29),
        ("RISE_WEDGE", 45, 44.4, 26),
        ("DBL_TOP", 58, 39.7, 23),
        ("BROAD_TOP", 8, 62.5, 6),
        ("ASC_TRI", 26, 34.6, 5),
    ],
    "BTC/USDT 30m": [
        ("RISE_WEDGE", 21, 66.7, 26),
        ("H&S", 6, 50.0, 11),
        ("TRI_TOP", 11, 36.4, 10),
        ("DBL_TOP", 33, 36.4, 10),
        ("SYM_TRI_BULL", 7, 42.9, 4),
    ],
    "BTC/USDT 1h": [
        ("RISE_WEDGE", 13, 76.9, 18),
        ("BROAD_BOT", 5, 100.0, 12),
        ("DBL_BOT", 16, 37.5, 6),
        ("DBL_TOP", 13, 46.2, 2),
    ],
    "ETH/USDT 1h": [
        ("DBL_TOP", 11, 54.5, 11),
        ("H&S", 5, 60.0, 11),
        ("TRI_TOP", 7, 71.4, 9),
        ("SYM_TRI_BEAR", 4, 100.0, 7),
        ("ASC_TRI", 10, 50.0, 3),
    ],
}

# =============================================================================
# RECOMENDACOES
# =============================================================================
RECOMENDACOES = """
===========================================================================
  RECOMENDACOES FINAIS
===========================================================================

  MELHOR PARA LUCRO:
    -> ETH/USDT 3m: $200 -> $529 (+164.6%) | MDD 6.6%

  MELHOR RISCO/RETORNO:
    -> ETH/USDT 30m: PF 2.05 | MDD 8.4%

  MENOR RISCO (MDD):
    -> BTC/USDT 1h: MDD 4.5% | +12.1%

  MELHOR EQUILIBRIO:
    -> ETH/USDT 5m: $200 -> $475 (+137.6%) | MDD 16.3%

  EVITAR:
    -> BTC/USDT 1h: lucro baixo (+12.1%)
    -> ETH/USDT 1h: lucro baixo (+11.6%)

  PADROES MAIS LUCRATIVOS:
    -> DESC_TRI: melhor no 3m (WR 58-64%)
    -> DBL_TOP: mais consistente em todos os TFs
    -> RISE_WEDGE: melhor no 30m (WR 66-77%)
    -> TRI_TOP: forte no 15m e 30m

  CONFIGURACAO ATUAL:
    -> Max 3 posicoes simultaneas
    -> 50% do saldo por posicao
    -> Stop: 50% do range da barra
    -> R:R 1:3
    -> Simbolos: BTC/USDT + ETH/USDT

===========================================================================
"""

# =============================================================================
# COMPARACAO: SIMPLES vs REALISTA
# =============================================================================
COMPARACAO = """
===========================================================================
  COMPARACAO: Backtest Simples (100%) vs Realista (50% x3)
===========================================================================

  Par/TF           Simples     Realista    Diferenca
  --------------------------------------------------
  ETH/USDT/3m       +57.9%      +164.6%     +106.7%  (melhorou)
  ETH/USDT/5m       +14.2%      +137.6%     +123.4%  (melhorou)
  BTC/USDT/3m       +16.0%      +118.3%     +102.3%  (melhorou)
  BTC/USDT/5m       +29.7%       +67.1%      +37.4%  (melhorou)
  ETH/USDT/15m      +76.6%       +48.1%      -28.4%  (piorou)
  BTC/USDT/15m      +90.6%       +32.2%      -58.4%  (piorou)
  ETH/USDT/30m      +47.7%       +47.7%        0.0%  (igual)
  BTC/USDT/30m     +130.8%       +23.6%     -107.2%  (piorou)
  ETH/USDT/1h       +59.7%       +11.6%      -48.1%  (piorou)
  BTC/USDT/1h       +25.2%       +12.1%      -13.1%  (piorou)

  CONCLUSAO:
  - Timeframes curtos (3m, 5m): Realista MELHORA (mais trades simultaneos)
  - Timeframes longos (15m, 30m, 1h): Realista PIORA (menos sinais)
  - MDD cai drasticamente no modo realista

===========================================================================
"""

if __name__ == '__main__':
    print(f"\n{'='*70}")
    print(f"  RESULTADO COMPLETO - BACKTEST REALISTA")
    print(f"  Max 3 pos | 50% cada | R:R 1:3 | 60 dias | $200")
    print(f"{'='*70}\n")

    print(f"  {'#':>2} {'Par/TF':<15} {'T/dia':>6} {'WR%':>6} {'PnL%':>8} {'PF':>5} {'MDD%':>6} {'$200->':>8}")
    print(f"  {'-'*70}")
    for r in RANKING_GERAL:
        print(f"  {r['#']:>2} {r['par']+'/'+r['tf']:<15} {r['trades_dia']:>5.1f} {r['wr']:>5.1f}% {r['pnl']:>7.1f}% {r['pf']:>5.2f} {r['mdd']:>5.1f}% ${r['saldo']:>7,}")

    print(COMPARACAO)
    print(RECOMENDACOES)
