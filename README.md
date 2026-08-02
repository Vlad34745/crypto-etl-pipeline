# Automated Crypto ETL Pipeline & Business Intelligence Dashboard

[![Crypto ETL Pipeline](https://github.com/Vlad34745/crypto-etl-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Vlad34745/crypto-etl-pipeline/actions/workflows/pipeline.yml)

An automated data pipeline (ETL) that extracts real-time cryptocurrency
market data via a REST API, maintains an incremental historical dataset,
and compiles a styled executive-ready dashboard inside Microsoft Excel.

![Dashboard preview](docs/dashboard-preview.png)
*Sample output — KPI summary, top gainer/loser table, and price trend chart, generated automatically by the pipeline.*

## 🚀 Key Features
* **Data Ingestion:** Connects to the CoinGecko Public API with built-in retry / rate-limit (429) handling.
* **Data Validation:** Sanity-checks every fetched snapshot (required columns, non-empty, no null prices) before it's allowed to touch the historical file.
* **Incremental Storage:** Appends new snapshots to a historical Excel log, safely deduplicated by `(symbol, snapshot_time)`.
* **Automated Backups with Retention:** Every run backs up the existing workbook to `backups/` before writing, and automatically prunes old backups (keeps the most recent `MAX_BACKUPS`, default 10).
* **Dashboard:** A styled "Emerald Light" executive sheet with KPI summary blocks and a Top Gainers / Top Losers table.
* **Structured Logging:** All pipeline activity is logged to both the console and `pipeline.log`.
* **Configurable:** Coin list, retry behavior, storage paths, and logging are all controlled via environment variables / `.env` — no code changes needed.
* **Tested:** Core logic (fetch/retry, cleaning, validation, merge/dedup, backup retention) is covered by `pytest` unit tests with the API mocked — no network access needed to run them.
* **CI:** GitHub Actions runs the test suite on every push/PR, and can run the pipeline itself on a schedule.

## 🛠️ Tech Stack
* **Language:** Python
* **Data Engineering:** Pandas
* **BI & Spreadsheet Engineering:** OpenPyXL
* **Config:** python-dotenv
* **Testing:** pytest
* **CI/CD:** GitHub Actions
* **Automation (optional local use):** Windows Batch Scripting (`.bat`)

---

## 💻 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/Vlad34745/crypto-etl-pipeline.git
cd crypto-etl-pipeline
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```
For running the test suite, also install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

### 4. (Optional) Configure
Copy `.env.example` to `.env` and edit any values you want to override
(tracked coins, retry settings, output paths, log level). If you skip
this step, sensible defaults are used automatically.
```bash
cp .env.example .env
```

### 5. Run the pipeline
```bash
python crypto_automation.py
```
When run in an interactive terminal, it first asks which coins to track:
```
Які монети відстежувати? (тікери через пробіл, напр. "btc eth sol"; Enter — залишити поточні [bitcoin]):
```
Type tickers separated by spaces (e.g. `btc eth sol`) and press Enter, or
just press Enter to keep whatever is set in `COIN_IDS`. This prompt is
automatically skipped in non-interactive environments (CI, cron, scheduled
`.bat` runs with no console attached) — those always use `COIN_IDS` from
`.env`/the environment.

Or, on Windows, double-click `run_pipeline.bat` — it activates the
virtual environment automatically and runs the pipeline for you (with the
same coin prompt, since it opens a normal console window).

### 6. Run the tests
```bash
pytest -v
```
All tests mock the CoinGecko API, so no network access or API key is required.

### 7. Output
A workbook named `crypto_history.xlsx` is generated (or updated) in the
project root, containing:
- **Dashboard** — KPI summary and the latest Top Gainer / Top Loser snapshot
- **Crypto Market Timeline** — the full historical log of every snapshot ever collected

Each run also saves a timestamped backup to `backups/` before writing new
data, keeping only the most recent `MAX_BACKUPS` copies. Activity is logged
to `pipeline.log`.

## ⚙️ Configuration
All settings live in `config.py` and can be overridden via environment
variables or a `.env` file (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `COIN_IDS` | `bitcoin` | Comma-separated CoinGecko coin IDs to track — see `.env.example` for a ready list of common coins to copy-paste |
| `API_URL` | CoinGecko markets endpoint | Data source URL |
| `RETRIES` | `3` | API retry attempts |
| `RETRY_DELAY_SECONDS` | `15` | Delay between retries |
| `OUTPUT_FILE` | `crypto_history.xlsx` | Workbook path |
| `BACKUP_DIR` | `backups` | Backup folder |
| `MAX_BACKUPS` | `10` | Number of backups to retain |
| `MIN_SNAPSHOT_INTERVAL_MINUTES` | `0` | Skip writing if the last snapshot is more recent than this (0 = always write) |
| `LOG_FILE` | `pipeline.log` | Log file path |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## 🗂️ Project Structure
```
crypto_automation.py    # Main pipeline (production script)
crypto_pipeline.ipynb   # Exploratory / development notebook (mirrors the script for interactive use)
config.py                # Central configuration (env-driven)
tests/                    # pytest unit tests (API mocked, no network needed)
.github/workflows/        # CI: tests on push/PR, scheduled pipeline runs
.env.example              # Template for local configuration
requirements.txt          # Runtime dependencies
requirements-dev.txt       # + testing dependencies
```

## 🤖 Continuous Integration
`.github/workflows/pipeline.yml` does two things:
1. **On every push/PR:** installs dependencies and runs `pytest`.
2. **On a schedule (every 6 hours) or manual trigger:** runs the pipeline
   and uploads the resulting `crypto_history.xlsx` as a downloadable
   workflow artifact (kept for 30 days). The workbook is *not* committed
   back to the repository — generated data files stay out of git history,
   consistent with `.gitignore`. For persistent scheduled history, point
   `OUTPUT_FILE` at cloud storage or a database instead of a local path.
