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


# --- Data source -----------------------------------------------------------
# Comma-separated CoinGecko coin IDs (not tickers) — e.g. "bitcoin,ethereum".
# See .env.example for a ready-to-copy list of common coin IDs, or use the
# interactive prompt (just run `python crypto_automation.py`) and type
# tickers like "btc eth sol" — they get resolved via TICKER_TO_COIN_ID below.
COIN_IDS = os.getenv("COIN_IDS", "bitcoin")
API_URL = os.getenv("API_URL", "https://api.coingecko.com/api/v3/coins/markets")

# Common ticker -> CoinGecko coin id, used to resolve what you type at the
# interactive coin-selection prompt. Not exhaustive — anything not listed
# here is assumed to already be a valid CoinGecko id and passed through as-is.
TICKER_TO_COIN_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "NEAR": "near",
    "TON": "the-open-network",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "LTC": "litecoin",
    "MATIC": "matic-network",
    "POL": "matic-network",
    "BNB": "binancecoin",
}

# --- Retry behaviour ---------------------------------------------------------
RETRIES = _int_env("RETRIES", 3)
RETRY_DELAY_SECONDS = _int_env("RETRY_DELAY_SECONDS", 15)

# --- Storage -----------------------------------------------------------------
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "crypto_history.xlsx")
BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
MAX_BACKUPS = _int_env("MAX_BACKUPS", 10)

# Skip writing a new snapshot if the last one is more recent than this
# many minutes ago (0 = always write, no throttling)
MIN_SNAPSHOT_INTERVAL_MINUTES = _int_env("MIN_SNAPSHOT_INTERVAL_MINUTES", 0)

# --- Logging -------------------------------------------------------------
LOG_FILE = os.getenv("LOG_FILE", "pipeline.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
