"""
Central configuration for the Crypto ETL Pipeline.

Values are read from environment variables (or a local .env file, if
python-dotenv is installed and a .env exists) with sensible defaults.
Copy .env.example to .env and edit it to override any setting without
touching the code.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional; if it's not installed we just fall back
    # to whatever is already in the environment / the hardcoded defaults.
    pass


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --- Data source -----------------------------------------------------------
# Comma-separated CoinPaprika coin IDs (e.g. "btc-bitcoin,eth-ethereum").
# CoinPaprika's free tier needs no API key and isn't blocked on CI/datacenter
# IPs the way CoinGecko/CryptoCompare's free tiers now are.
COIN_IDS = os.getenv("COIN_IDS", "btc-bitcoin")
API_URL = os.getenv("API_URL", "https://api.coinpaprika.com/v1/tickers")

# Common ticker -> CoinPaprika coin id, used to resolve what you type at the
# interactive coin-selection prompt. Not exhaustive — anything not listed
# here is assumed to already be a valid CoinPaprika id and passed through as-is.
TICKER_TO_COIN_ID = {
    "BTC": "btc-bitcoin",
    "ETH": "eth-ethereum",
    "SOL": "sol-solana",
    "NEAR": "near-near-protocol",
    "TON": "ton-toncoin",
    "ADA": "ada-cardano",
    "XRP": "xrp-xrp",
    "DOGE": "doge-dogecoin",
    "DOT": "dot-polkadot",
    "AVAX": "avax-avalanche",
    "LINK": "link-chainlink",
    "LTC": "ltc-litecoin",
    "MATIC": "matic-polygon",
    "POL": "pol-polygon-ecosystem-token",
    "BNB": "bnb-binance-coin",
}

# --- Retry behaviour ---------------------------------------------------------
RETRIES = _int_env("RETRIES", 3)
RETRY_DELAY_SECONDS = _int_env("RETRY_DELAY_SECONDS", 15)

# --- Storage -----------------------------------------------------------------
# DB_FILE is the source of truth for historical data. OUTPUT_FILE (the Excel
# workbook) is regenerated from it on every run — it's a report, not storage.
DB_FILE = os.getenv("DB_FILE", "crypto_history.db")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "crypto_history.xlsx")
BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
MAX_BACKUPS = _int_env("MAX_BACKUPS", 10)

# Skip writing a new snapshot if the last one is more recent than this
# many minutes ago (0 = always write, no throttling)
MIN_SNAPSHOT_INTERVAL_MINUTES = _int_env("MIN_SNAPSHOT_INTERVAL_MINUTES", 0)

# --- Alerts (optional) --------------------------------------------------------
# Sends a Telegram message when a coin's 24h change crosses this threshold.
# Disabled unless both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ALERT_THRESHOLD_PERCENT = _float_env("ALERT_THRESHOLD_PERCENT", 5.0)

# --- Logging -------------------------------------------------------------
LOG_FILE = os.getenv("LOG_FILE", "pipeline.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
