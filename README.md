# Automated Crypto ETL Pipeline & Business Intelligence Dashboard

[![Crypto ETL Pipeline](https://github.com/Vlad34745/crypto-etl-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Vlad34745/crypto-etl-pipeline/actions/workflows/pipeline.yml)
[![codecov](https://codecov.io/gh/Vlad34745/crypto-etl-pipeline/branch/main/graph/badge.svg)](https://codecov.io/gh/Vlad34745/crypto-etl-pipeline)

An automated data pipeline (ETL) that extracts real-time cryptocurrency
market data via a REST API, stores it in SQLite, and compiles a styled
executive-ready dashboard inside Microsoft Excel — with optional Telegram
price alerts.

![Dashboard preview](docs/dashboard-preview.png)
*Sample output — KPI summary, top gainer/loser table, and price trend chart, generated automatically by the pipeline.*

## 🚀 Key Features
* **Data Ingestion:** Connects to the CoinGecko Public API with built-in retry / rate-limit (429) handling.
* **Data Validation:** Sanity-checks every fetched snapshot (required columns, non-empty, no null prices) before it's allowed to touch storage.
* **SQLite Storage:** `crypto_history.db` is the source of truth — incremental inserts, a real uniqueness constraint on `(symbol, snapshot_time)`, no full-file rewrites as history grows.
* **Excel Reporting:** `crypto_history.xlsx` is regenerated from the database on every run — a report artifact, not storage. Sorted by coin name, then time.
* **Automated Backups with Retention:** Every run backs up the database to `backups/` before writing, and automatically prunes old backups (keeps the most recent `MAX_BACKUPS`, default 10).
* **Dashboard:** A styled "Emerald Light" executive sheet with KPI blocks, a Top Gainers/Losers table, and an embedded price-trend line chart.
* **Interactive Coin Selection:** Run it in a terminal and it asks which coins to track (`btc eth sol`) — no need to look up CoinGecko IDs. Skipped automatically in CI/cron.
* **Snapshot Throttling:** Optional minimum interval between snapshots, so you can run the pipeline often without flooding the history.
* **Telegram Alerts (optional):** Sends a message when a coin's 24h change crosses a configurable threshold.
* **Structured Logging:** All pipeline activity is logged to both the console and `pipeline.log`.
* **Configurable:** Coins, retry behavior, storage paths, throttling, alerts, and logging are all controlled via environment variables / `.env` — no code changes needed.
* **Tested:** 29 `pytest` unit/integration tests (API and Telegram mocked, no network needed), enforcing ≥70% coverage in CI.
* **CI:** GitHub Actions lints (`ruff`), tests (with coverage), and can run the pipeline itself on a schedule. Dependabot keeps dependencies and Actions up to date.

## 🛠️ Tech Stack
* **Language:** Python
* **Data Engineering:** Pandas, SQLite
* **BI & Spreadsheet Engineering:** OpenPyXL
* **Config:** python-dotenv
* **Testing:** pytest, pytest-cov
* **Linting:** ruff
* **CI/CD:** GitHub Actions, Dependabot
* **Alerts:** Telegram Bot API
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
(tracked coins, retry settings, storage paths, throttling, Telegram alerts,
log level). If you skip this step, sensible defaults are used automatically.
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
automatically skipped in non-interactive environments (CI, cron) — those
always use `COIN_IDS` from `.env`/the environment. You can also force this
explicitly with `python crypto_automation.py --no-prompt`.

Or, on Windows, double-click `run_pipeline.bat` — it activates the virtual
environment automatically and runs the pipeline for you (with the same coin
prompt, since it opens a normal console window).

### 6. Run the tests
```bash
pytest -v --cov=. --cov-report=term-missing
```
All tests mock the CoinGecko API and Telegram, so no network access or API
keys are required.

### 7. Output
- **`crypto_history.db`** (SQLite) — the source of truth for all historical snapshots.
- **`crypto_history.xlsx`** — regenerated from the database every run:
  - **Dashboard** — KPI summary, Top Gainer/Loser table, price trend chart
  - **Crypto Market Timeline** — the full historical log, sorted by coin then time

Each run also saves a timestamped backup of the database to `backups/`
before writing new data, keeping only the most recent `MAX_BACKUPS` copies.
Activity is logged to `pipeline.log`.

## 📲 Telegram Alerts (optional)
To get a message when a coin's 24h change crosses a threshold:
1. Message [@BotFather](https://t.me/BotFather) on Telegram, create a bot, and copy its token.
2. Send your new bot any message, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser to find your `chat.id`.
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` (and `ALERT_THRESHOLD_PERCENT` if you want something other than the 5% default).

Leaving either value blank disables alerts entirely — the pipeline runs
exactly as before. For scheduled runs via GitHub Actions, set these as
repository secrets (`Settings → Secrets and variables → Actions`) instead
of committing them; the workflow already passes them through.

## ⚙️ Configuration
All settings live in `config.py` and can be overridden via environment
variables or a `.env` file (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `COIN_IDS` | `bitcoin` | Comma-separated CoinGecko coin IDs to track — see `.env.example` for a ready list of common coins to copy-paste |
| `API_URL` | CoinGecko markets endpoint | Data source URL |
| `RETRIES` | `3` | API retry attempts |
| `RETRY_DELAY_SECONDS` | `15` | Delay between retries |
| `DB_FILE` | `crypto_history.db` | SQLite database path (source of truth) |
| `OUTPUT_FILE` | `crypto_history.xlsx` | Excel report path (regenerated every run) |
| `BACKUP_DIR` | `backups` | Backup folder |
| `MAX_BACKUPS` | `10` | Number of backups to retain |
| `MIN_SNAPSHOT_INTERVAL_MINUTES` | `0` | Skip writing if the last snapshot is more recent than this (0 = always write) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | *(blank)* | Enable Telegram alerts by setting both |
| `ALERT_THRESHOLD_PERCENT` | `5.0` | 24h change (absolute %) that triggers an alert |
| `LOG_FILE` | `pipeline.log` | Log file path |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## 🗂️ Project Structure
```
crypto_automation.py    # Main pipeline (production script)
db.py                    # SQLite persistence layer (source of truth)
crypto_pipeline.ipynb   # Exploratory / development notebook (mirrors the script for interactive use)
config.py                # Central configuration (env-driven)
tests/                    # pytest unit/integration tests (API + Telegram mocked)
.github/workflows/        # CI: lint, test+coverage, scheduled pipeline runs
.github/dependabot.yml    # Weekly dependency + GitHub Actions update PRs
.env.example              # Template for local configuration
requirements.txt          # Runtime dependencies
requirements-dev.txt       # + testing/linting dependencies
```

## 🤖 Continuous Integration
`.github/workflows/pipeline.yml`:
1. **`lint`** — runs `ruff check .` on every push/PR.
2. **`test`** — installs dependencies (pip-cached) and runs the full test suite with coverage, failing the build if coverage drops below 70%.
3. **`run-pipeline`** — on a schedule (every 6 hours) or manual trigger, runs the pipeline (Telegram secrets passed through if configured) and uploads the resulting database + workbook as a downloadable artifact (kept for 30 days). Neither is committed back to the repository — generated data files stay out of git history, consistent with `.gitignore`.

**Coverage badge:** powered by [Codecov](https://about.codecov.io/) (free for
public repos) — see the setup steps below. Until it's connected, the badge
shows "unknown"; `--cov-fail-under=70` in CI enforces the threshold either way.

Dependabot (`.github/dependabot.yml`) opens a PR weekly for outdated pip
packages and GitHub Actions versions.
