import ccxt
import pandas as pd
import numpy as np
import time
import sys
import os
from datetime import datetime

# Adicionar pasta atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import *
from strategy import generate_signals, get_current_signal, calculate_indicators
from risk import RiskManager


class Bot:
    """Bot de trading - Elephant + Wick Bar"""

    def __init__(self):
        self.exchange = self._init_exchange()
        self.risk = RiskManager()
        self.last_bar_index = {}
        self.running = True

        perfil = PERFIL_ATIVO.upper()
        cor = Colors.GREEN if PERFIL_ATIVO == "agressivo" else Colors.YELLOW

        print(f"\n{Colors.CYAN}{'='*60}")
        print(f"  BOT ELEPHANT + WICK BAR")
        print(f"  Perfil: {cor}{Colors.BOLD}{perfil}{Colors.RESET}{Colors.CYAN}")
        print(f"  Exchange: {EXCHANGE}")
        print(f"  Symbols: {', '.join(SYMBOLS)}")
        print(f"  Timeframe: {TIMEFRAME}")
        print(f"  Stop: {STOP_MODE} | R:R 1:{RR_RATIO}")
        print(f"  Conta: ${ACCOUNT_SIZE:,.0f} | Posicao: {POSITION_SIZE_PCT*100:.0f}%")
        print(f"  Min Bar: {MIN_BAR_RATIO}x | Cooldown: {MIN_BARS_BETWEEN}b")
        print(f"  1a Elefante: {'Sim' if ONLY_FIRST_ELEPHANT else 'Nao'} | EMA20: {'On' if EMA20_FILTER else 'Off'}")
        print(f"{'='*60}{Colors.RESET}\n")

    def _init_exchange(self):
        """Inicializa exchange"""
        config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }
        if API_KEY:
            config['apiKey'] = API_KEY
            config['secret'] = API_SECRET

        if EXCHANGE == 'binance':
            return ccxt.binance(config)
        elif EXCHANGE == 'bybit':
            return ccxt.bybit(config)
        else:
            return ccxt.binance(config)

    def fetch_ohlcv(self, symbol, limit=200):
        """Busca dados OHLCV"""
        data = self.exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=limit)
        df = pd.DataFrame(data, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        df.set_index('ts', inplace=True)
        return df

    def print_signal(self, signal, symbol):
        """Imprime sinal encontrado"""
        color = Colors.GREEN if signal.direction == 'buy' else Colors.RED
        emoji = "^" if signal.direction == 'buy' else "v"

        print(f"{color}{'='*60}{Colors.RESET}")
        print(f"{color}{Colors.BOLD}  SINAL: {signal.label} {symbol}{Colors.RESET}")
        print(f"{color}  Direcao: {signal.direction.upper()} {emoji}{Colors.RESET}")
        print(f"{color}  Entrada: ${signal.price:,.2f}{Colors.RESET}")
        print(f"{color}  Stop:    ${signal.stop:,.2f}{Colors.RESET}")

        risk = abs(signal.price - signal.stop)
        target = signal.price + risk * RR_RATIO if signal.direction == 'buy' else signal.price - risk * RR_RATIO
        print(f"{color}  Target:  ${target:,.2f} (R:R 1:{RR_RATIO}){Colors.RESET}")
        print(f"{color}  Range:   ${signal.bar_range:,.2f}{Colors.RESET}")
        print(f"{color}{'='*60}{Colors.RESET}")

    def print_trade(self, trade):
        """Imprime resultado de trade"""
        if trade['pnl'] > 0:
            color = Colors.GREEN
            emoji = "+"
        else:
            color = Colors.RED
            emoji = ""

        print(f"{color}  {emoji}{trade['pnl']:.2f}% | "
              f"{trade['label']} | "
              f"Entry: ${trade['entry_price']:,.2f} | "
              f"Exit: ${trade['exit_price']:,.2f} | "
              f"{trade['reason']}{Colors.RESET}")

    def print_stats(self):
        """Imprime estatisticas"""
        stats = self.risk.get_stats()
        print(f"\n{Colors.CYAN}{'='*60}")
        print(f"  ESTATISTICAS")
        print(f"  Balance: ${stats['balance']:,.2f}")
        print(f"  Trades: {stats['total_trades']} | W: {stats['wins']} | L: {stats['losses']}")
        print(f"  Win Rate: {stats['win_rate']}%")
        print(f"  PnL: {stats['total_pnl']:+.2f}%")
        print(f"  Profit Factor: {stats['profit_factor']}")
        print(f"  Max Drawdown: {stats['max_drawdown']:.2f}%")
        print(f"{'='*60}{Colors.RESET}\n")

    def run_once(self):
        """Executa uma verificacao"""
        for symbol in SYMBOLS:
            try:
                df = self.fetch_ohlcv(symbol, limit=200)
                df = calculate_indicators(df)
                signals = generate_signals(df)

                # Verificar ultima barra
                last_idx = len(df) - 1
                if symbol in self.last_bar_index and self.last_bar_index[symbol] == last_idx:
                    continue

                self.last_bar_index[symbol] = last_idx

                # Sinais na ultima barra
                for sig in signals:
                    if sig.index == last_idx - 1:  # Barra completa anterior
                        if self.risk.can_trade():
                            self.print_signal(sig, symbol)
                            qty = self.risk.calculate_position_size(sig.price, sig.stop)
                            pos = self.risk.open_position(sig, qty)
                            pos['symbol'] = symbol
                            print(f"  POSICAO ABERTA: {qty} @ ${sig.price:,.2f}")

            except Exception as e:
                print(f"  ERRO {symbol}: {e}")

        # Verificar saidas
        for symbol in SYMBOLS:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                exits = self.risk.check_exit(ticker['high'], ticker['low'])
                for trade in exits:
                    self.print_trade(trade)
            except Exception as e:
                pass

    def run_loop(self, interval=10):
        """Loop principal"""
        print(f"{Colors.YELLOW}  Bot iniciado. Verificando a cada {interval}s...{Colors.RESET}")
        print(f"{Colors.YELLOW}  Ctrl+C para parar{Colors.RESET}\n")

        while self.running:
            try:
                self.run_once()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.running = False
                print(f"\n{Colors.YELLOW}  Bot parado.{Colors.RESET}")
                self.print_stats()
            except Exception as e:
                print(f"\n{Colors.RED}  ERRO: {e}{Colors.RESET}")
                time.sleep(interval)

    def show_signals(self):
        """Mostra sinais atuais sem executar"""
        print(f"\n{Colors.CYAN}{'='*60}")
        print(f"  SINAIS ATUAIS")
        print(f"{'='*60}{Colors.RESET}")

        for symbol in SYMBOLS:
            try:
                df = self.fetch_ohlcv(symbol, limit=200)
                df = calculate_indicators(df)
                signals = generate_signals(df)

                recent = [s for s in signals if s.index >= len(df) - 5]

                print(f"\n  {symbol}: {len(recent)} sinais recentes")
                for sig in recent[-5:]:
                    color = Colors.GREEN if sig.direction == 'buy' else Colors.RED
                    print(f"    {color}{sig.label} | {sig.direction} | "
                          f"${sig.price:,.2f} | Stop: ${sig.stop:,.2f}{Colors.RESET}")

            except Exception as e:
                print(f"  ERRO {symbol}: {e}")


def main():
    bot = Bot()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'signals':
            bot.show_signals()
        elif cmd == 'once':
            bot.run_once()
            bot.print_stats()
        elif cmd == 'stats':
            bot.print_stats()
        else:
            print(f"Uso: python bot.py [signals|once|stats]")
    else:
        bot.run_loop()


if __name__ == '__main__':
    main()
