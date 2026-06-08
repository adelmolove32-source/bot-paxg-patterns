import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ccxt
import pandas as pd
import numpy as np
import time
import asyncio
import logging
import threading
from datetime import datetime

from config import *
from strategy import generate_signals, calculate_indicators

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def start_health_server():
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def health():
        return 'Bot is running', 200

    @app.route('/health')
    def health_check():
        return 'OK', 200

    port = int(os.environ.get("PORT", "10000"))
    thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True)
    thread.start()
    logger.info(f"Health server started on port {port}")


def fetch_ohlcv(symbol, timeframe, limit=200):
    exchange = ccxt.binance({'enableRateLimit': True})
    data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df.set_index('ts', inplace=True)
    return df


def format_signal(sig, symbol, capital=200, trades=0, wins=0):
    arrow = "BUY" if sig.direction == 'buy' else "SELL"
    color = "🟢" if sig.direction == 'buy' else "🔴"

    risk = abs(sig.price - sig.stop)
    if sig.direction == 'buy':
        target = sig.price + risk * RR_RATIO
    else:
        target = sig.price - risk * RR_RATIO

    rr_pct = ((target - sig.price) / sig.price * 100) if sig.direction == 'buy' else ((sig.price - target) / sig.price * 100)
    sl_pct = ((sig.price - sig.stop) / sig.price * 100) if sig.direction == 'buy' else ((sig.stop - sig.price) / sig.price * 100)

    entry_usd = capital * POSITION_SIZE_PCT
    qty = entry_usd / sig.price
    risk_usd = entry_usd * sl_pct / 100
    gain_usd = entry_usd * rr_pct / 100

    wr = (wins / trades * 100) if trades > 0 else 0
    tf = TIMEFRAMES.get(symbol, TIMEFRAME)

    msg = (
        f"{color} *{arrow}* `{sig.label}` *{symbol}*\n\n"
        f"Entrada: `${sig.price:,.2f}`\n"
        f"Stop:    `${sig.stop:,.2f}` (-{sl_pct:.2f}%)\n"
        f"Target:  `${target:,.2f}` (+{rr_pct:.2f}%)\n"
        f"R:R  1:{RR_RATIO}\n\n"
        f"--- SIMULACAO ---\n"
        f"Banca: ${capital:.2f}\n"
        f"Entrada: ${entry_usd:.2f} ({qty:.6f})\n"
        f"Risco: ${risk_usd:.2f}\n"
        f"Ganho: ${gain_usd:.2f}\n"
        f"Trades: {trades} | WR: {wr:.0f}%\n"
        f"TF: {tf}"
    )
    return msg


def format_signals_list(signals, symbol, df=None):
    if not signals:
        return f"*{symbol}* - Nenhum sinal recente"

    msg = f"*{symbol}* - Ultimos {len(signals)} sinais:\n\n"
    for sig in signals[-8:]:
        arrow = "BUY" if sig.direction == 'buy' else "SELL"
        color = "🟢" if sig.direction == 'buy' else "🔴"
        if df is not None and sig.index < len(df):
            ts = (df.index[sig.index] - pd.Timedelta(hours=3)).strftime('%d/%m %H:%M')
        else:
            ts = "?"
        msg += f"{color} `{ts}` `{sig.label}` {arrow} @ `${sig.price:,.2f}`\n"
    return msg


class TelegramBot:
    def __init__(self):
        self.last_bar_index = {}
        self.sent_signals = set()
        self.running = True
        self.start_time = datetime.now()
        self.total_signals_sent = 0
        self.capital = {s: ACCOUNT_SIZE for s in SYMBOLS}
        self.trades_count = {s: 0 for s in SYMBOLS}
        self.wins_count = {s: 0 for s in SYMBOLS}
        self.open_positions = {s: [] for s in SYMBOLS}

    def check_positions(self, symbol, current_high, current_low):
        """Verifica posicoes abertas e fecha se atingiu TP/SL"""
        closed = []
        remaining = []
        
        for pos in self.open_positions[symbol]:
            exit_price = None
            reason = None
            
            if pos['direction'] == 'buy':
                if current_low <= pos['stop']:
                    exit_price = pos['stop']
                    reason = 'SL'
                elif current_high >= pos['target']:
                    exit_price = pos['target']
                    reason = 'TP'
            else:
                if current_high >= pos['stop']:
                    exit_price = pos['stop']
                    reason = 'SL'
                elif current_low <= pos['target']:
                    exit_price = pos['target']
                    reason = 'TP'
            
            if exit_price:
                if pos['direction'] == 'buy':
                    pnl_pct = (exit_price - pos['entry']) / pos['entry'] * 100
                else:
                    pnl_pct = (pos['entry'] - exit_price) / pos['entry'] * 100
                
                pnl_usd = pos['entry_usd'] * pnl_pct / 100
                self.capital[symbol] += pnl_usd
                self.trades_count[symbol] += 1
                if pnl_usd > 0:
                    self.wins_count[symbol] += 1
                
                closed.append({
                    'symbol': symbol,
                    'direction': pos['direction'],
                    'entry': pos['entry'],
                    'exit': exit_price,
                    'pnl_pct': round(pnl_pct, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'reason': reason,
                    'capital': round(self.capital[symbol], 2)
                })
            else:
                remaining.append(pos)
        
        self.open_positions[symbol] = remaining
        return closed

    def check_signals(self):
        new_signals = []
        for symbol in SYMBOLS:
            try:
                tf = TIMEFRAMES.get(symbol, TIMEFRAME)
                df = fetch_ohlcv(symbol, tf, limit=200)
                df = calculate_indicators(df)
                signals = generate_signals(df)

                last_idx = len(df) - 1
                if symbol in self.last_bar_index and self.last_bar_index[symbol] == last_idx:
                    continue
                self.last_bar_index[symbol] = last_idx

                for sig in signals:
                    if sig.index == last_idx - 1:
                        sig_key = f"{symbol}_{sig.label}_{sig.index}"
                        if sig_key not in self.sent_signals:
                            risk = abs(sig.price - sig.stop)
                            if sig.direction == 'buy':
                                target = sig.price + risk * RR_RATIO
                            else:
                                target = sig.price - risk * RR_RATIO

                            rr_pct = abs(target - sig.price) / sig.price * 100
                            if rr_pct < 0.50:
                                continue

                            self.sent_signals.add(sig_key)
                            new_signals.append((sig, symbol))
                            
                            risk = abs(sig.price - sig.stop)
                            if sig.direction == 'buy':
                                target = sig.price + risk * RR_RATIO
                            else:
                                target = sig.price - risk * RR_RATIO
                            
                            entry_usd = self.capital[symbol] * POSITION_SIZE_PCT
                            
                            self.open_positions[symbol].append({
                                'entry': sig.price,
                                'stop': sig.stop,
                                'target': target,
                                'direction': sig.direction,
                                'entry_usd': entry_usd,
                                'label': sig.label
                            })

            except Exception as e:
                logger.error(f"Erro {symbol}: {e}")

        return new_signals


async def cmd_start(update, context):
    await update.message.reply_text(
        f"*Bot Elephant + Wick Bar*\n\n"
        f"Perfis: {PERFIL_ATIVO}\n"
        f"Symbols: {', '.join(SYMBOLS)}\n"
        f"BTC: 3m | ETH: 5m\n"
        f"R:R 1:{RR_RATIO} | Stop: {STOP_MODE}\n\n"
        f"*Comandos:*\n"
        f"/signals - Sinais atuais\n"
        f"/status - Status do bot\n"
        f"/saldo - Saldo simulado\n"
        f"/relatorio - Relatorio completo\n"
        f"/backtest - Resultado dos 60d\n"
        f"/parar - Parar monitoramento\n"
        f"/iniciar - Iniciar monitoramento\n\n"
        f"Relatorio automatico a cada 1 hora.",
        parse_mode='Markdown'
    )


async def cmd_signals(update, context):
    await update.message.reply_text("Buscando sinais...")
    for symbol in SYMBOLS:
        try:
            tf = TIMEFRAMES.get(symbol, TIMEFRAME)
            df = fetch_ohlcv(symbol, tf, limit=200)
            df = calculate_indicators(df)
            signals = generate_signals(df)
            recent = [s for s in signals if s.index >= len(df) - 10]
            filtered = []
            for s in recent:
                risk = abs(s.price - s.stop)
                if s.direction == 'buy':
                    target = s.price + risk * RR_RATIO
                else:
                    target = s.price - risk * RR_RATIO
                rr_pct = abs(target - s.price) / s.price * 100
                if rr_pct >= 0.50:
                    filtered.append(s)
            msg = format_signals_list(filtered, symbol, df)
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"Erro {symbol}: {e}")


async def cmd_status(update, context):
    bot = context.bot_data.get('bot_instance')
    uptime = datetime.now() - bot.start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)

    capital_info = ""
    for symbol in SYMBOLS:
        cap = bot.capital[symbol]
        trades = bot.trades_count[symbol]
        wins = bot.wins_count[symbol]
        wr = (wins / trades * 100) if trades > 0 else 0
        pnl = cap - ACCOUNT_SIZE
        open_count = len(bot.open_positions[symbol])
        tf = TIMEFRAMES.get(symbol, TIMEFRAME)
        capital_info += f"{symbol} ({tf}): ${cap:.2f} ({pnl:+.2f}) | {trades} trades | WR: {wr:.0f}% | Abertas: {open_count}\n"

    await update.message.reply_text(
        f"*Status do Bot*\n\n"
        f"Uptime: {hours}h {minutes}m\n"
        f"Sinais enviados: {bot.total_signals_sent}\n"
        f"Intervalo: {TELEGRAM_INTERVAL}s\n"
        f"Rodando: {'Sim' if bot.running else 'Nao'}\n\n"
        f"*Simulacao:*\n"
        f"{capital_info}",
        parse_mode='Markdown'
    )


async def cmd_backtest(update, context):
    await update.message.reply_text("Rodando backtest... (pode demorar)")
    try:
        from backtest import run_backtest, calc_metrics
        from collections import Counter

        msg = "*BACKTEST 60d - Patterns R:R 1:3*\n\n"
        for symbol in SYMBOLS:
            for tf in ['3m', '5m']:
                df = fetch_ohlcv(symbol, tf, days=60)
                trades = run_backtest(df, 'patterns')
                if not trades:
                    continue
                m = calc_metrics(trades)
                per_day = m['t'] / 60
                msg += (
                    f"*{symbol} {tf}*: {m['t']} trades ({per_day:.0f}/dia)\n"
                    f"WR: {m['wr']}% | PnL: {m['pnl']:+.2f}% | PF: {m['pf']:.2f} | MDD: {m['mdd']:.2f}%\n\n"
                )
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Erro no backtest: {e}")


async def cmd_parar(update, context):
    bot = context.bot_data.get('bot_instance')
    bot.running = False
    await update.message.reply_text("Monitoramento parado.")


async def cmd_iniciar(update, context):
    bot = context.bot_data.get('bot_instance')
    bot.running = True
    await update.message.reply_text("Monitoramento iniciado.")


async def cmd_saldo(update, context):
    bot = context.bot_data.get('bot_instance')
    
    msg = "*SALDO SIMULADO*\n\n"
    total = 0
    for symbol in SYMBOLS:
        cap = bot.capital[symbol]
        pnl = cap - ACCOUNT_SIZE
        trades = bot.trades_count[symbol]
        wins = bot.wins_count[symbol]
        wr = (wins / trades * 100) if trades > 0 else 0
        open_count = len(bot.open_positions[symbol])
        total += cap
        
        emoji = "+" if pnl >= 0 else ""
        msg += f"*{symbol}*\n"
        msg += f"  Banca: ${cap:.2f} ({emoji}{pnl:.2f})\n"
        msg += f"  Trades: {trades} | WR: {wr:.0f}%\n"
        msg += f"  Posicoes abertas: {open_count}\n\n"
    
    total_pnl = total - (ACCOUNT_SIZE * len(SYMBOLS))
    emoji = "+" if total_pnl >= 0 else ""
    msg += f"*TOTAL: ${total:.2f} ({emoji}{total_pnl:.2f})*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_relatorio(update, context):
    bot = context.bot_data.get('bot_instance')
    
    msg = "*RELATORIO*\n\n"
    total = 0
    for symbol in SYMBOLS:
        cap = bot.capital[symbol]
        trades = bot.trades_count[symbol]
        wins = bot.wins_count[symbol]
        pnl = cap - ACCOUNT_SIZE
        wr = (wins / trades * 100) if trades > 0 else 0
        open_count = len(bot.open_positions[symbol])
        tf = TIMEFRAMES.get(symbol, TIMEFRAME)
        total += cap

        emoji = "+" if pnl >= 0 else ""
        msg += f"*{symbol} ({tf})*\n"
        msg += f"Banca: ${cap:.2f} ({emoji}{pnl:.2f})\n"
        msg += f"Trades: {trades} | WR: {wr:.0f}%\n"
        msg += f"Abertas: {open_count}\n\n"

    total_pnl = total - (ACCOUNT_SIZE * len(SYMBOLS))
    emoji = "+" if total_pnl >= 0 else ""
    msg += f"*TOTAL: ${total:.2f} ({emoji}{total_pnl:.2f})*"

    await update.message.reply_text(msg, parse_mode='Markdown')


async def hourly_report(context):
    bot = context.bot_data.get('bot_instance')
    if not bot.running:
        return

    uptime = datetime.now() - bot.start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)

    now = datetime.now().strftime("%H:%M")

    msg = (
        f"*BOT ATIVO*\n\n"
        f"Hora: {now}\n"
        f"Uptime: {hours}h {minutes}m\n"
        f"Sinais enviados: {bot.total_signals_sent}\n"
        f"Monitorando: {', '.join(SYMBOLS)}"
    )

    await context.bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=msg,
        parse_mode='Markdown'
    )


async def monitor_loop(context):
    bot = context.bot_data.get('bot_instance')
    if not bot.running:
        return

    for symbol in SYMBOLS:
        try:
            ticker = context.bot_data.get('exchange', {}).get(symbol, {})
            if not ticker:
                from telegram_bot import fetch_ohlcv
                exchange = ccxt.binance({'enableRateLimit': True})
                ticker = exchange.fetch_ticker(symbol)
            
            high = ticker.get('high', 0)
            low = ticker.get('low', 0)
            
            closed = bot.check_positions(symbol, high, low)
            for trade in closed:
                emoji = "+" if trade['pnl_usd'] > 0 else ""
                msg = (
                    f"{'✅' if trade['pnl_usd'] > 0 else '❌'} *TRADE FECHADO* {trade['symbol']}\n\n"
                    f"Direcao: {trade['direction'].upper()}\n"
                    f"Entry: ${trade['entry']:,.2f}\n"
                    f"Exit: ${trade['exit']:,.2f} ({trade['reason']})\n"
                    f"PnL: {emoji}${trade['pnl_usd']:.2f} ({emoji}{trade['pnl_pct']:.2f}%)\n"
                    f"Banca: ${trade['capital']:.2f}"
                )
                await context.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=msg,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Erro check positions {symbol}: {e}")

    new_signals = bot.check_signals()
    for sig, symbol in new_signals:
        msg = format_signal(
            sig, symbol,
            capital=bot.capital[symbol],
            trades=bot.trades_count[symbol],
            wins=bot.wins_count[symbol]
        )
        try:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode='Markdown'
            )
            bot.total_signals_sent += 1
            logger.info(f"Signal sent: {sig.label} {symbol}")
        except Exception as e:
            logger.error(f"Erro ao enviar: {e}")


def main():
    from telegram import Update, BotCommand
    from telegram.ext import Application, CommandHandler, ContextTypes

    start_health_server()

    bot_instance = TelegramBot()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.bot_data['bot_instance'] = bot_instance

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("signals", cmd_signals))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("backtest", cmd_backtest))
    app.add_handler(CommandHandler("parar", cmd_parar))
    app.add_handler(CommandHandler("iniciar", cmd_iniciar))
    app.add_handler(CommandHandler("saldo", cmd_saldo))
    app.add_handler(CommandHandler("relatorio", cmd_relatorio))

    app.job_queue.run_repeating(
        monitor_loop,
        interval=TELEGRAM_INTERVAL,
        first=5
    )

    app.job_queue.run_repeating(
        hourly_report,
        interval=3600,
        first=10
    )

    print(f"\n{'='*60}")
    print(f"  BOT TELEGRAM - Elephant + Wick Bar")
    print(f"  Symbols: {', '.join(SYMBOLS)}")
    print(f"  Timeframe: {TIMEFRAME}")
    print(f"  Intervalo: {TELEGRAM_INTERVAL}s")
    print(f"  Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"{'='*60}\n")

    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
