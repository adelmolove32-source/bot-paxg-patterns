from config import *


class RiskManager:
    """Gerencia risco e posicoes"""

    def __init__(self, account_size=ACCOUNT_SIZE, position_pct=POSITION_SIZE_PCT):
        self.account_size = account_size
        self.position_pct = position_pct
        self.balance = account_size
        self.positions = []
        self.trade_history = []
        self.max_drawdown = 0
        self.peak_balance = account_size

    def calculate_position_size(self, entry_price, stop_loss):
        """
        Calcula tamanho da posicao baseado no risco.
        Metade da conta por trade.
        """
        position_value = self.balance * self.position_pct
        qty = position_value / entry_price
        return round(qty, 8)

    def calculate_risk(self, entry_price, stop_loss, qty):
        """Calcula risco em USD"""
        risk_per_unit = abs(entry_price - stop_loss)
        total_risk = risk_per_unit * qty
        return round(total_risk, 2)

    def can_trade(self):
        """Verifica se pode abrir nova posicao"""
        if len(self.positions) >= 3:
            return False
        if self.balance < self.account_size * 0.2:
            return False
        return True

    def open_position(self, signal, qty):
        """Registra abertura de posicao"""
        position = {
            'symbol': signal.symbol if hasattr(signal, 'symbol') else 'UNKNOWN',
            'direction': signal.direction,
            'entry_price': signal.price,
            'stop_loss': signal.stop,
            'target': self._calculate_target(signal.price, signal.stop, signal.direction),
            'qty': qty,
            'label': signal.label,
            'bar_range': signal.bar_range,
            'type': signal.type,
            'open_time': None
        }
        self.positions.append(position)
        return position

    def close_position(self, index, exit_price, reason):
        """Registra fechamento de posicao"""
        if index >= len(self.positions):
            return None

        pos = self.positions.pop(index)

        if pos['direction'] == 'buy':
            pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
        else:
            pnl = (pos['entry_price'] - exit_price) / pos['entry_price'] * 100

        # Atualizar balance
        trade_value = pos['qty'] * pos['entry_price']
        trade_pnl = trade_value * pnl / 100
        self.balance += trade_pnl

        # Atualizar drawdown
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        dd = (self.peak_balance - self.balance) / self.peak_balance * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd

        trade = {
            **pos,
            'exit_price': exit_price,
            'pnl': round(pnl, 2),
            'pnl_usd': round(trade_pnl, 2),
            'reason': reason,
            'exit_time': None
        }
        self.trade_history.append(trade)
        return trade

    def check_exit(self, current_high, current_low):
        """Verifica se alguma posicao deve ser fechada"""
        exits = []
        i = 0
        while i < len(self.positions):
            pos = self.positions[i]
            exit_price = None
            reason = None

            if pos['direction'] == 'buy':
                if current_low <= pos['stop_loss']:
                    exit_price = pos['stop_loss']
                    reason = 'STOP_LOSS'
                elif current_high >= pos['target']:
                    exit_price = pos['target']
                    reason = 'TAKE_PROFIT'
            else:
                if current_high >= pos['stop_loss']:
                    exit_price = pos['stop_loss']
                    reason = 'STOP_LOSS'
                elif current_low <= pos['target']:
                    exit_price = pos['target']
                    reason = 'TAKE_PROFIT'

            if exit_price:
                trade = self.close_position(i, exit_price, reason)
                if trade:
                    exits.append(trade)
            else:
                i += 1

        return exits

    def get_stats(self):
        """Retorna estatisticas"""
        if not self.trade_history:
            return {
                'total_trades': 0, 'wins': 0, 'losses': 0,
                'win_rate': 0, 'total_pnl': 0, 'avg_pnl': 0,
                'profit_factor': 0, 'max_drawdown': 0,
                'balance': self.balance
            }

        wins = [t for t in self.trade_history if t['pnl'] > 0]
        losses = [t for t in self.trade_history if t['pnl'] <= 0]

        total_pnl = sum(t['pnl'] for t in self.trade_history)
        avg_pnl = total_pnl / len(self.trade_history)

        win_sum = sum(t['pnl'] for t in wins)
        loss_sum = abs(sum(t['pnl'] for t in losses))
        pf = win_sum / loss_sum if loss_sum > 0 else 999

        return {
            'total_trades': len(self.trade_history),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(len(wins) / len(self.trade_history) * 100, 1),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(avg_pnl, 2),
            'profit_factor': round(min(pf, 999), 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'balance': round(self.balance, 2)
        }

    def _calculate_target(self, entry, stop, direction):
        risk = abs(entry - stop)
        if direction == 'buy':
            return entry + risk * RR_RATIO
        else:
            return entry - risk * RR_RATIO
