# Automated Crypto ETL Pipeline & Business Intelligence Dashboard

An institutional-grade data pipeline (ETL) designed to extract real-time cryptocurrency telemetry via REST APIs, maintain an incremental historical dataset, and compile a polished executive-ready financial dashboard inside Microsoft Excel.

Designed specifically for non-technical stakeholders, this application bypasses complex terminal environments by utilizing a seamless **1-click automation handler (.bat)**.

## 🚀 Key Architectural Features
* **Robust Data Ingestion Engine:** Integrated secure API connectors with built-in rate-limit (429) tolerance and response validation.
* **Incremental Storage Architecture:** Implemented an automated local database wrapper that safely appends new telemetry snapshots while preserving data history and tracking temporal logs.
* **Automated Backups:** Every run creates a timestamped backup of the existing workbook in `backups/` before writing new data, so a failed or partial run never destroys prior history.
* **Corporate Dashboard Automation:** Generates a high-end "Emerald Light" executive spreadsheet complete with KPI summary blocks and real-time market movement tables (Top Gainers & Losers).
* **Enterprise Formatting Standards:** Fully automated visual treatments featuring custom number masks (`$#,##0.00` and `0.00%`), structural split-pane frozen views, and strictly calculated auto-column dimensions to completely eradicate Excel `###` overflows.

## 🛠️ Infrastructure & Tech Stack
* **Language:** Python
* **Data Engineering:** Pandas (Data structuring, deduplication, time-slice evaluation)
* **BI & Spreadsheet Engineering:** OpenPyXL (Dynamic styling, borders, colors, font mapping, custom metrics)
* **Automation:** Windows Batch Scripting (`.bat`)

---

## 💻 Installation & Setup

Follow these quick steps to deploy and run the automation pipeline locally:

### 1. Clone the Repository
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

### 4. Run the pipeline
```bash
python crypto_automation.py
```
Or, on Windows, simply double-click `run_pipeline.bat` — it activates the virtual environment automatically and runs the pipeline for you.

### 5. Output
A workbook named `crypto_history.xlsx` is generated (or updated) in the project root, containing:
- **Dashboard** — KPI summary and the latest Top Gainer / Top Loser snapshot
- **Crypto Market Timeline** — the full historical log of every snapshot ever collected

Each run also saves a timestamped backup of the previous workbook to `backups/` before writing new data.

## ⚙️ Configuration
The tracked coins can be changed by editing the `COIN_IDS` variable near the top of `crypto_automation.py` (uses CoinGecko coin IDs, comma-separated).