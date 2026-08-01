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
COIN_IDS = os.getenv("COIN_IDS", "bitcoin,ethereum,solana,near,the-open-network")
API_URL = os.getenv("API_URL", "https://api.coingecko.com/api/v3/coins/markets")

# --- Retry behaviour ---------------------------------------------------------
RETRIES = _int_env("RETRIES", 3)
RETRY_DELAY_SECONDS = _int_env("RETRY_DELAY_SECONDS", 15)

# --- Storage -----------------------------------------------------------------
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "crypto_history.xlsx")
BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
MAX_BACKUPS = _int_env("MAX_BACKUPS", 10)

# --- Logging -------------------------------------------------------------
LOG_FILE = os.getenv("LOG_FILE", "pipeline.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
