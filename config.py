import os

# ============================================================
# CONFIGURACAO - ESTRATEGIA ELEPHANT + WICK BAR
# ============================================================

PERFIL_ATIVO = os.environ.get("PERFIL_ATIVO", "agressivo")

# ============================================================
# PERFIS
# ============================================================
PERFIS = {
    "agressivo": {
        "MIN_BAR_RATIO": 1.5,
        "MIN_BARS_BETWEEN": 1,
        "ONLY_FIRST_ELEPHANT": False,
        "WICK_ONLY_BEAR": False,
        "EMA20_FILTER": False,
        "MAX_TRADES_PER_DAY": 999,
        "COOLDOWN_AFTER_LOSS": 0,
    },
    "conservador": {
        "MIN_BAR_RATIO": 2.0,
        "MIN_BARS_BETWEEN": 3,
        "ONLY_FIRST_ELEPHANT": True,
        "WICK_ONLY_BEAR": False,
        "EMA20_FILTER": True,
        "MAX_TRADES_PER_DAY": 10,
        "COOLDOWN_AFTER_LOSS": 2,
    }
}

# ============================================================
# CONFIGURACAO BASE (comum aos dois perfis)
# ============================================================

# API
API_KEY = os.environ.get("API_KEY", "")
API_SECRET = os.environ.get("API_SECRET", "")

# Exchange
EXCHANGE = os.environ.get("EXCHANGE", "binance")
SYMBOLS = ["BTC/USDT", "ETH/USDT"]
TIMEFRAMES = {"BTC/USDT": "3m", "ETH/USDT": "5m"}
TIMEFRAME = "3m"

# Risco
ACCOUNT_SIZE = int(os.environ.get("ACCOUNT_SIZE", "200"))
POSITION_SIZE_PCT = 0.333
STOP_MODE = os.environ.get("STOP_MODE", "half")
RR_RATIO = 3

# Estrategia
ELEPHANT_BODY_PCT = 0.55
ELEPHANT_LOOKBACK = 10
ELEPHANT_PLUS_TOP = 0.2
WICK_MIN_RATIO = 1.0

# Timeframe em minutos
TF_MINUTES = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "1h": 60}

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_INTERVAL = int(os.environ.get("TELEGRAM_INTERVAL", "10"))

# ============================================================
# APLICAR PERFIL ATIVO
# ============================================================
_perfil = PERFIS[PERFIL_ATIVO]

MIN_BAR_RATIO = _perfil["MIN_BAR_RATIO"]
MIN_BARS_BETWEEN = _perfil["MIN_BARS_BETWEEN"]
ONLY_FIRST_ELEPHANT = _perfil["ONLY_FIRST_ELEPHANT"]
WICK_ONLY_BEAR = _perfil["WICK_ONLY_BEAR"]
EMA20_FILTER = _perfil["EMA20_FILTER"]
MAX_TRADES_PER_DAY = _perfil["MAX_TRADES_PER_DAY"]
COOLDOWN_AFTER_LOSS = _perfil["COOLDOWN_AFTER_LOSS"]

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
