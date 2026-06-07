import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest import fetch_ohlcv
from patterns import detect_all_patterns
from strategy import calculate_indicators

df = fetch_ohlcv('ETH/USDT', '5m', days=7)
df = calculate_indicators(df)

signals = detect_all_patterns(df)

print(f"\nSINAIS ENCONTRADOS (ultimos 10):")
print(f"{'='*85}")
print(f"{'Data/Hora':20s} | {'Padrao':15s} | {'Direcao':8s} | {'Entry':>10s} | {'Stop':>10s} | {'Target':>10s}")
print(f"{'-'*85}")

for sig in signals[-10:]:
    idx = sig['index']
    dt = df.index[idx]  # data real da barra
    
    print(f"{str(dt):20s} | {sig['label']:15s} | {sig['direction']:8s} | ${sig['entry']:>9.2f} | ${sig['stop']:>9.2f} | ${sig['target']:>9.2f}")
