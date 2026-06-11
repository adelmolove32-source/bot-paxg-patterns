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

from config_paxg import *
from strategy_paxg import generate_signals, calculate_indicators

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def start_health_server():
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def health():
        return 'Bot PAXG running', 200

    @app.route('/health')
    def health_check():
        return 'OK', 200

    port = int(os.environ.get("PORT", "10000"))
    thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True)
    thread.start()
    logger.info(f"Health server started on port {port}")


def fetch_ohlcv(symbol, timeframe, limit=200):
    exchange = ccxt.binance({'enableRateLimit': True})
    time.sleep(1)
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
        f"TF: {TIMEFRAME}"
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
        self.last_bar_index = None
        self.sent_signals = set()
        self.running = True
        self.start_time = datetime.now()
        self.total_signals_sent = 0
        self.capital = ACCOUNT_SIZE
        self.trades_count = 0
        self.wins_count = 0
        self.open_positions = []

    def check_positions(self, current_high, current_low):
        closed = []
        remaining = []

        for pos in self.open_positions:
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
                self.capital += pnl_usd
                self.trades_count += 1
                if pnl_usd > 0:
                    self.wins_count += 1

                closed.append({
                    'symbol': SYMBOL,
                    'direction': pos['direction'],
                    'entry': pos['entry'],
                    'exit': exit_price,
                    'pnl_pct': round(pnl_pct, 2),
                    'pnl_usd': round(pnl_usd, 2),
                    'reason': reason,
                    'capital': round(self.capital, 2)
                })
            else:
                remaining.append(pos)

        self.open_positions = remaining
        return closed

    def check_signals(self):
        new_signals = []
        try:
            df = fetch_ohlcv(SYMBOL, TIMEFRAME, limit=200)
            df = calculate_indicators(df)
            signals = generate_signals(df)

            last_idx = len(df) - 1
            if self.last_bar_index == last_idx:
                return []
            self.last_bar_index = last_idx

            for sig in signals:
                if sig.index >= last_idx - 10 and sig.index < last_idx:
                    sig_key = f"{sig.label}_{sig.index}"
                    if sig_key not in self.sent_signals:
                        risk = abs(sig.price - sig.stop)
                        if sig.direction == 'buy':
                            target = sig.price + risk * RR_RATIO
                        else:
                            target = sig.price - risk * RR_RATIO

                        rr_pct = risk * RR_RATIO / sig.price * 100
                        logger.info(f"Signal: {sig.label} rr_pct={rr_pct:.2f}%")
                        if MIN_RR_PCT > 0 and rr_pct < MIN_RR_PCT:
                            logger.info(f"Filtered: rr_pct {rr_pct:.2f}% < {MIN_RR_PCT}%")
                            continue

                        self.sent_signals.add(sig_key)
                        new_signals.append(sig)

                        current_price = df['c'].iloc[-1]
                        entry_valid = True
                        if sig.direction == 'buy' and current_price > sig.price * 1.003:
                            entry_valid = False
                        if sig.direction == 'sell' and current_price < sig.price * 0.997:
                            entry_valid = False

                        if entry_valid and len(self.open_positions) < MAX_OPEN_POSITIONS:
                            entry_usd = self.capital * POSITION_SIZE_PCT
                            self.open_positions.append({
                                'entry': sig.price,
                                'stop': sig.stop,
                                'target': target,
                                'direction': sig.direction,
                                'entry_usd': entry_usd,
                                'label': sig.label
                            })

        except Exception as e:
            logger.error(f"Erro: {e}")

        return new_signals


async def cmd_start(update, context):
    await update.message.reply_text(
        f"*Bot PAXG Patterns*\n\n"
        f"Par: {SYMBOL}\n"
        f"Timeframe: {TIMEFRAME}\n"
        f"R:R 1:{RR_RATIO} | Stop: {STOP_MODE}\n"
        f"Padroes: {len(ENABLED_PATTERNS)}\n\n"
        f"*Comandos:*\n"
        f"/signals - Sinais atuais\n"
        f"/status - Status do bot\n"
        f"/saldo - Saldo simulado\n"
        f"/relatorio - Relatorio completo\n"
        f"/parar - Parar monitoramento\n"
        f"/iniciar - Iniciar monitoramento\n\n"
        f"Relatorio automatico a cada 1 hora.",
        parse_mode='Markdown'
    )


async def cmd_signals(update, context):
    await update.message.reply_text("Buscando sinais...")
    try:
        df = fetch_ohlcv(SYMBOL, TIMEFRAME, limit=200)
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
            if MIN_RR_PCT == 0 or rr_pct >= MIN_RR_PCT:
                filtered.append(s)
        msg = format_signals_list(filtered, SYMBOL, df)
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")


async def cmd_status(update, context):
    bot = context.bot_data.get('bot_instance')
    uptime = datetime.now() - bot.start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)

    cap = bot.capital
    trades = bot.trades_count
    wins = bot.wins_count
    wr = (wins / trades * 100) if trades > 0 else 0
    pnl = cap - ACCOUNT_SIZE
    open_count = len(bot.open_positions)

    await update.message.reply_text(
        f"*Status do Bot*\n\n"
        f"Uptime: {hours}h {minutes}m\n"
        f"Sinais enviados: {bot.total_signals_sent}\n"
        f"Intervalo: {TELEGRAM_INTERVAL}s\n"
        f"Rodando: {'Sim' if bot.running else 'Nao'}\n\n"
        f"*Simulacao:*\n"
        f"{SYMBOL} ({TIMEFRAME}): ${cap:.2f} ({pnl:+.2f}) | {trades} trades | WR: {wr:.0f}% | Abertas: {open_count}",
        parse_mode='Markdown'
    )


async def cmd_saldo(update, context):
    bot = context.bot_data.get('bot_instance')

    cap = bot.capital
    pnl = cap - ACCOUNT_SIZE
    trades = bot.trades_count
    wins = bot.wins_count
    wr = (wins / trades * 100) if trades > 0 else 0
    open_count = len(bot.open_positions)

    emoji = "+" if pnl >= 0 else ""
    msg = (
        f"*SALDO SIMULADO*\n\n"
        f"*{SYMBOL}*\n"
        f"  Banca: ${cap:.2f} ({emoji}{pnl:.2f})\n"
        f"  Trades: {trades} | WR: {wr:.0f}%\n"
        f"  Posicoes abertas: {open_count}\n\n"
        f"*TOTAL: ${cap:.2f} ({emoji}{pnl:.2f})*"
    )

    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_relatorio(update, context):
    bot = context.bot_data.get('bot_instance')

    cap = bot.capital
    trades = bot.trades_count
    wins = bot.wins_count
    pnl = cap - ACCOUNT_SIZE
    wr = (wins / trades * 100) if trades > 0 else 0
    open_count = len(bot.open_positions)

    emoji = "+" if pnl >= 0 else ""
    msg = (
        f"*RELATORIO*\n\n"
        f"*{SYMBOL} ({TIMEFRAME})*\n"
        f"Banca: ${cap:.2f} ({emoji}{pnl:.2f})\n"
        f"Trades: {trades} | WR: {wr:.0f}%\n"
        f"Abertas: {open_count}\n\n"
        f"*TOTAL: ${cap:.2f} ({emoji}{pnl:.2f})*"
    )

    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_parar(update, context):
    bot = context.bot_data.get('bot_instance')
    bot.running = False
    await update.message.reply_text("Monitoramento parado.")


async def cmd_iniciar(update, context):
    bot = context.bot_data.get('bot_instance')
    bot.running = True
    await update.message.reply_text("Monitoramento iniciado.")


async def cmd_test(update, context):
    msg = (
        "🟢 *BUY* `RISE_WEDGE` *PAXG/USDT*\n\n"
        "Entrada: `$3,250.00`\n"
        "Stop:    `$3,230.00` (-0.62%)\n"
        "Target:  `$3,310.00` (+1.85%)\n"
        "R:R  1:3\n\n"
        "--- SIMULACAO ---\n"
        "Banca: $200.00\n"
        "Entrada: $66.60 (0.020492)\n"
        "Risco: $0.41\n"
        "Ganho: $1.23\n"
        "Trades: 5 | WR: 60%\n"
        "TF: 30m"
    )
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
        f"*BOT PAXG ATIVO*\n\n"
        f"Hora: {now}\n"
        f"Uptime: {hours}h {minutes}m\n"
        f"Sinais enviados: {bot.total_signals_sent}\n"
        f"Monitorando: {SYMBOL} {TIMEFRAME}"
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

    try:
        df = fetch_ohlcv(SYMBOL, TIMEFRAME, limit=200)
        df = calculate_indicators(df)

        high = df['h'].iloc[-1]
        low = df['l'].iloc[-1]

        closed = bot.check_positions(high, low)
        for trade in closed:
            emoji = "+" if trade['pnl_usd'] > 0 else ""
            msg = (
                f"{'✅' if trade['pnl_usd'] > 0 else '❌'} *TRADE FECHADO*\n\n"
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

        signals = generate_signals(df)
        last_idx = len(df) - 1
        if bot.last_bar_index != last_idx:
            bot.last_bar_index = last_idx
            for sig in signals:
                if sig.index >= last_idx - 10 and sig.index < last_idx:
                    sig_key = f"{sig.label}_{sig.index}"
                    if sig_key not in bot.sent_signals:
                        risk = abs(sig.price - sig.stop)
                        if sig.direction == 'buy':
                            target = sig.price + risk * RR_RATIO
                        else:
                            target = sig.price - risk * RR_RATIO

                        rr_pct = risk * RR_RATIO / sig.price * 100
                        logger.info(f"Signal: {sig.label} rr_pct={rr_pct:.2f}%")
                        if MIN_RR_PCT > 0 and rr_pct < MIN_RR_PCT:
                            logger.info(f"Filtered: rr_pct {rr_pct:.2f}% < {MIN_RR_PCT}%")
                            continue

                        bot.sent_signals.add(sig_key)
                        msg = format_signal(sig, SYMBOL, capital=bot.capital, trades=bot.trades_count, wins=bot.wins_count)
                        try:
                            await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode='Markdown')
                            bot.total_signals_sent += 1
                            logger.info(f"Signal sent: {sig.label}")
                        except Exception as e:
                            logger.error(f"Erro ao enviar: {e}")

                        entry_usd = bot.capital * POSITION_SIZE_PCT
                        entry_valid = True
                        current_price = df['c'].iloc[-1]
                        if sig.direction == 'buy' and current_price > sig.price * 1.003:
                            entry_valid = False
                        if sig.direction == 'sell' and current_price < sig.price * 0.997:
                            entry_valid = False
                        if entry_valid and len(bot.open_positions) < MAX_OPEN_POSITIONS:
                            bot.open_positions.append({
                                'entry': sig.price, 'stop': sig.stop, 'target': target,
                                'direction': sig.direction, 'entry_usd': entry_usd, 'label': sig.label
                            })

    except Exception as e:
        logger.error(f"Erro: {e}")


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
    app.add_handler(CommandHandler("parar", cmd_parar))
    app.add_handler(CommandHandler("iniciar", cmd_iniciar))
    app.add_handler(CommandHandler("saldo", cmd_saldo))
    app.add_handler(CommandHandler("relatorio", cmd_relatorio))
    app.add_handler(CommandHandler("test", cmd_test))

    app.job_queue.run_repeating(
        monitor_loop,
        interval=TELEGRAM_INTERVAL,
        first=30
    )

    app.job_queue.run_repeating(
        hourly_report,
        interval=3600,
        first=10
    )

    print(f"\n{'='*60}")
    print(f"  BOT PAXG - Patterns 30m")
    print(f"  Symbol: {SYMBOL}")
    print(f"  Timeframe: {TIMEFRAME}")
    print(f"  R:R 1:{RR_RATIO} | Stop: {STOP_MODE}")
    print(f"  Padroes: {', '.join(ENABLED_PATTERNS)}")
    print(f"  Intervalo: {TELEGRAM_INTERVAL}s")
    print(f"  Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"{'='*60}\n")

    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
