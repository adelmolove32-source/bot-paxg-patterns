import os

# ============================================================
# CONFIGURACAO - BOT PAXG/USDT 30m PATTERNS
# ============================================================

# API
API_KEY = os.environ.get("API_KEY", "")
API_SECRET = os.environ.get("API_SECRET", "")

# Exchange
EXCHANGE = os.environ.get("EXCHANGE", "binance")
SYMBOL = "PAXG/USDT"
TIMEFRAME = "30m"

# Risco
ACCOUNT_SIZE = int(os.environ.get("ACCOUNT_SIZE", "200"))
POSITION_SIZE_PCT = 0.333
STOP_MODE = os.environ.get("STOP_MODE", "half")
RR_RATIO = 3
MIN_RR_PCT = 0.25
MAX_OPEN_POSITIONS = 3

# Filtros de padroes (melhores do backtest)
ENABLED_PATTERNS = [
    "RISE_WEDGE",      # WR 75% - Top 1
    "SYM_TRI_BEAR",    # WR 70% - Top 2
    "SYM_TRI_BULL",    # WR 68% - Top 3
    "BROAD_TOP",       # WR 62% - Top 4
    "ASC_TRI",         # WR 50% - Top 5
    "DBL_TOP",         # WR 36% - consistente
    "TRI_TOP",         # WR 43% - consistente
]

# Timeframe em minutos
TF_MINUTES = {"30m": 30, "1h": 60}

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_INTERVAL = int(os.environ.get("TELEGRAM_INTERVAL", "30"))

# Cores do terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
