# %%
import datetime
import time
import requests
import pandas as pd
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import numpy as np


# %% [markdown]
# # Step 1: Automated Data Ingestion & API Integration
# In this step, the pipeline dynamically connects to the CoinGecko Public API to fetch live, real-time cryptocurrency market data. The raw JSON response is parsed, filtered, and transformed into a structured Pandas DataFrame with execution timestamps for complete auditability.

# %%
COIN_IDS = "bitcoin,ethereum,solana,near,the-open-network"

def fetch_crypto_data_with_retry(retries=3, delay=15):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": COIN_IDS,
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:
                print(f"[Warning] Rate limit hit (429). Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Error] Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None
    return None

# %%
# Execute safe data ingestion
raw_json = fetch_crypto_data_with_retry()

if raw_json:
    df_raw = pd.DataFrame(raw_json)
    columns_to_keep = ["name", "symbol", "current_price", "market_cap", "total_volume", "price_change_percentage_24h"]
    df_clean = df_raw[columns_to_keep].copy()
    
    # NORMALIZATION: Convert API percentages (e.g. 0.48) into true decimal fractions (0.0048) right here
    df_clean["price_change_percentage_24h"] = df_clean["price_change_percentage_24h"] / 100.0
    
    df_clean["snapshot_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_clean["symbol"] = df_clean["symbol"].str.upper()

    print("Data ingestion completed. Percentages normalized globally.")
    #display(df_clean)
else:
    print("Pipeline Failure: Unable to fetch data.")

# %% [markdown]
# # Step 2: Incremental Data Accumulation & History Tracking
# To prevent data loss from overwriting, this component implements an incremental storage logic. It safely detects if a tracking database already exists, loads the historical timeline, appends the new snapshot, and eliminates any operational duplicates before committing back to the master storage.

# %%
OUTPUT_FILE = "crypto_history.xlsx"
BACKUP_DIR = "backups"

# 1. Automated Corporate Backup Sequence
if os.path.exists(OUTPUT_FILE):
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{BACKUP_DIR}/crypto_history_backup_{timestamp_str}.xlsx"
    
    # Create an exact replica of the database file
    import shutil
    shutil.copyfile(OUTPUT_FILE, backup_filename)
    print(f"Secure database snapshot saved to backup storage: '{backup_filename}'")

# %%
# 2. Historical Data Incremental Merging
if os.path.exists(OUTPUT_FILE):
    print(f"Loading historical stream from '{OUTPUT_FILE}'...")
    df_historical = pd.read_excel(OUTPUT_FILE, sheet_name="Crypto Market Timeline")
    df_updated = pd.concat([df_historical, df_clean], ignore_index=True)
    df_updated.drop_duplicates(subset=["symbol", "snapshot_time"], keep="first", inplace=True)
else:
    print("No legacy tracking file discovered. Initializing database schema...")
    df_updated = df_clean.copy()

print(f"Sync complete. Total data array rows: {len(df_updated)}")

# %% [markdown]
# # Step 3: Executive BI Reporting & Advanced Corporate Excel Styling
# This final component transforms raw tabular data into an executive-ready business report using `openpyxl`. It automatically applies professional financial typography (Segoe UI), dynamic column width auto-fitting, currency formatting with proper thousand separators, and an elegant emerald/mint corporate header. To ensure seamless scrolling through long market timelines, the main header grid row is dynamically frozen.

# %%
OUTPUT_FILE = "crypto_history.xlsx"

# =========================================================================
# STEP 1: SAVE RAW HISTORICAL DATA TO EXCEL
# =========================================================================
# Writing updated DataFrame safely to the logging sheet
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df_updated.to_excel(writer, sheet_name="Crypto Market Timeline", index=False)

wb = openpyxl.load_workbook(OUTPUT_FILE)
ws_timeline = wb["Crypto Market Timeline"]

# Re-creating or clearing the Dashboard sheet
if "Dashboard" in wb.sheetnames:
    del wb["Dashboard"]
ws_dash = wb.create_sheet("Dashboard", index=0)

# %%
# =========================================================================
# STEP 2: CORPORATE BI DESIGN & FORMATTING (EMERALD LIGHT STYLE)
# =========================================================================
FONT_NAME = "Segoe UI"
HEADER_COLOR = "0A5C36"  # Premium Emerald Green
ACCENT_BG = "E8F5E9"     # Soft Mint Green for KPI blocks

font_title = Font(name=FONT_NAME, size=18, bold=True, color=HEADER_COLOR)
font_subtitle = Font(name=FONT_NAME, size=10, italic=True, color="555555")
font_section = Font(name=FONT_NAME, size=12, bold=True, color="333333")
font_kpi_label = Font(name=FONT_NAME, size=10, bold=True, color="666666")
font_kpi_value = Font(name=FONT_NAME, size=14, bold=True, color="111111")
font_header = Font(name=FONT_NAME, size=11, bold=True, color="FFFFFF")
font_data = Font(name=FONT_NAME, size=11, color="333333")

# Professional Trend Colors
font_positive = Font(name=FONT_NAME, size=11, color="0E622F", bold=True) # Rich Dark Green
font_negative = Font(name=FONT_NAME, size=11, color="9C0006", bold=True) # Deep Red

fill_header = PatternFill(start_color=HEADER_COLOR, end_color=HEADER_COLOR, fill_type="solid")
fill_kpi = PatternFill(start_color=ACCENT_BG, end_color=ACCENT_BG, fill_type="solid")
thin_side = Side(style="thin", color="D3D3D3")
border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

align_center = Alignment(horizontal="center", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")

# --- 1. BUILDING THE EXECUTIVE DASHBOARD ---
ws_dash.views.sheetView[0].showGridLines = True
ws_dash["A1"] = "Crypto Analytics Control Panel"
ws_dash["A1"].font = font_title
ws_dash["A2"] = f"Automated pipeline telemetry — Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
ws_dash["A2"].font = font_subtitle

# KPI Metrics Cards Block
kpi_configs = [
    ("A4", "DATASET LOG VOLUME", f"{len(df_updated)} Rows"), 
    ("D4", "MONITORED TICKERS", f"{df_updated['symbol'].nunique()} Unique Coins")
]

for target_cell, label, val in kpi_configs:
    start_col, start_row = target_cell[0], int(target_cell[1])
    end_col = chr(ord(start_col) + 1)
    
    ws_dash.merge_cells(f"{start_col}{start_row}:{end_col}{start_row}")
    ws_dash[f"{start_col}{start_row}"] = label
    ws_dash[f"{start_col}{start_row}"].font = font_kpi_label
    ws_dash[f"{start_col}{start_row}"].alignment = align_center
    
    ws_dash.merge_cells(f"{start_col}{start_row+1}:{end_col}{start_row+1}")
    ws_dash[f"{start_col}{start_row+1}"] = val
    ws_dash[f"{start_col}{start_row+1}"].font = font_kpi_value
    ws_dash[f"{start_col}{start_row+1}"].alignment = align_center
    
    for r in range(start_row, start_row+2):
        for c in range(ord(start_col)-64, ord(end_col)-63):
            ws_dash.cell(row=r, column=c).fill = fill_kpi
            ws_dash.cell(row=r, column=c).border = border_cell

# Market Leaders Analytics Table
ws_dash["A7"] = "Market Performance Leaders (Latest Snapshot Window)"
ws_dash["A7"].font = font_section

headers_dash = ["Insight Metric", "Asset Name", "Ticker", "Current Value", "24h Shift %"]
for idx, h_text in enumerate(headers_dash, start=1):
    c = ws_dash.cell(row=8, column=idx, value=h_text)
    c.font = font_header
    c.fill = fill_header
    c.alignment = align_center
    c.border = border_cell

# Isolate the latest telemetry slice to extract performance leaders
latest_time = df_updated["snapshot_time"].max()
df_latest_snapshot = df_updated[df_updated["snapshot_time"] == latest_time]

top_gainer = df_latest_snapshot.sort_values(by="price_change_percentage_24h", ascending=False).iloc[0]
top_loser = df_latest_snapshot.sort_values(by="price_change_percentage_24h", ascending=True).iloc[0]

leaders_rows = [
    ("Top Market Gainer", top_gainer["name"], top_gainer["symbol"], top_gainer["current_price"], top_gainer["price_change_percentage_24h"]),
    ("Top Market Loser", top_loser["name"], top_loser["symbol"], top_loser["current_price"], top_loser["price_change_percentage_24h"])
]

for r_idx, row_data in enumerate(leaders_rows, start=9):
    for c_idx, val in enumerate(row_data, start=1):
        cell = ws_dash.cell(row=r_idx, column=c_idx, value=val)
        cell.font = font_data
        cell.border = border_cell
        if c_idx == 1:
            cell.font = Font(name=FONT_NAME, size=11, bold=True)
        elif c_idx == 3:
            cell.alignment = align_center
        elif c_idx == 4:
            cell.number_format = "$#,##0.00"
            cell.alignment = align_right
        elif c_idx == 5:
            # Safe parsing to normalize scale if percentage is already divided
            if cell.value is not None and abs(cell.value) > 2.0 and not str(cell.value).startswith("0."):
                cell.value = cell.value / 100.0
            cell.number_format = "0.00%"
            cell.alignment = align_right
            cell.font = font_positive if val > 0 else font_negative

# --- 2. FORMATTING THE HISTORICAL LOGS SHEET (TIMELINE) ---
ws_timeline.row_dimensions[1].height = 26
ws_timeline.freeze_panes = "A2"

for cell in ws_timeline[1]:
    cell.fill = fill_header
    cell.font = font_header
    cell.alignment = align_center

for row in ws_timeline.iter_rows(min_row=2, max_row=ws_timeline.max_row, min_col=1, max_col=ws_timeline.max_column):
    for cell in row:
        cell.font = font_data
        cell.border = border_cell
        col_name = ws_timeline.cell(row=1, column=cell.column).value
        
        # Financial metrics alignment and masks
        if col_name == "current_price":
            cell.alignment = align_right
            cell.number_format = "$#,##0.00"
        elif col_name in ["market_cap", "total_volume"]:
            cell.alignment = align_right
            cell.number_format = "$#,##0"
            
        # Percentage scaling safety and conditional styling
        elif col_name == "price_change_percentage_24h":
            cell.alignment = align_right
            if cell.value is not None and abs(cell.value) > 2.0 and not str(cell.value).startswith("0."):
                cell.value = cell.value / 100.0
            cell.number_format = "0.00%"
            if cell.value is not None:
                cell.font = font_positive if cell.value > 0 else font_negative
                
        elif col_name in ["symbol", "snapshot_time"]:
            cell.alignment = align_center
        else:
            cell.alignment = align_left
            
# --- 3. AUTO-COLUMN WIDTH ADJUSTMENTS (PREVENTING ### ERRORS) ---
financial_cols = {"C": 16, "D": 22, "E": 22}
for ws in [ws_dash, ws_timeline]:
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        if ws == ws_timeline and col_letter in financial_cols:
            ws.column_dimensions[col_letter].width = financial_cols[col_letter]
        else:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col_letter].width = max(max_len + 5, 14)

# %%
wb.save(OUTPUT_FILE)
print("SUCCESS: Executive English version of Emerald Dashboard deployed safely!")


