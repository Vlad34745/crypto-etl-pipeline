# Automated Crypto ETL Pipeline & Business Intelligence Dashboard

An institutional-grade data pipeline (ETL) designed to extract real-time cryptocurrency telemetry via REST APIs, maintain an incremental historical dataset, and compile a polished executive-ready financial dashboard inside Microsoft Excel.

Designed specifically for non-technical stakeholders, this application bypasses complex terminal environments by utilizing a seamless **1-click automation handler (.bat)**.

## 🚀 Key Architectural Features
* **Robust Data Ingestion Engine:** Integrated secure API connectors with built-in rate-limit (429) tolerance and response validation.
* **Incremental Storage Architecture:** Implemented an automated local database wrapper that safely appends new telemetry snapshots while preserving data history and tracking temporal logs.
* **Corporate Dashboard Automation:** Generates a high-end "Emerald Light" executive spreadsheet sheet complete with KPI summary blocks and real-time market movement tables (Top Gainers & Losers).
* **Enterprise Formatting Standards:** Fully automated visual treatments featuring custom number masks (`$#,##0.00` and `0.00%`), structural split-pane frozen views, and strictly calculated auto-column dimensions to completely eradicate Excel `###` overflows.

## 🛠️ Infrastructure & Tech Stack
* **Language:** Python
* **Data Engineering:** Pandas (Data structuring, deduplication, time-slice evaluation)
* **BI & Spreadsheet Engineering:** OpenPyxl (Dynamic styling, borders, colors, font mapping, custom metrics)
* **Automation:** Windows Batch Scripting (`.bat`)

---

## 💻 Installation & Setup

Follow these quick steps to deploy and run the automation pipeline locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/Vlad34745/crypto-etl-pipeline.git](https://github.com/Vlad34745/crypto-etl-pipeline.git)
cd crypto-etl-pipeline