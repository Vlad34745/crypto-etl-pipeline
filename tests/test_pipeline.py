"""
Unit tests for crypto_automation.py.

Run with:
    pytest

No real network calls are made — the CoinGecko API is mocked.
"""

import os
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import crypto_automation as pipeline  # noqa: E402


SAMPLE_RAW_JSON = [
    {
        "id": "bitcoin",
        "name": "Bitcoin",
        "symbol": "btc",
        "current_price": 65000.0,
        "market_cap": 1_280_000_000_000,
        "total_volume": 30_000_000_000,
        "price_change_percentage_24h": 2.5,
    },
    {
        "id": "ethereum",
        "name": "Ethereum",
        "symbol": "eth",
        "current_price": 3500.0,
        "market_cap": 420_000_000_000,
        "total_volume": 15_000_000_000,
        "price_change_percentage_24h": -1.2,
    },
]


# --- fetch_crypto_data_with_retry -------------------------------------------
def test_fetch_success_returns_json():
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = SAMPLE_RAW_JSON
    mock_response.raise_for_status.return_value = None

    with patch("crypto_automation.requests.get", return_value=mock_response):
        result = pipeline.fetch_crypto_data_with_retry(retries=3, delay=0)

    assert result == SAMPLE_RAW_JSON


def test_fetch_retries_on_429_then_gives_up():
    mock_response = Mock(status_code=429)

    with patch("crypto_automation.requests.get", return_value=mock_response) as mock_get, \
         patch("crypto_automation.time.sleep", return_value=None):
        result = pipeline.fetch_crypto_data_with_retry(retries=3, delay=0)

    assert result is None
    assert mock_get.call_count == 3


def test_fetch_returns_none_on_persistent_network_error():
    with patch("crypto_automation.requests.get", side_effect=pipeline.requests.exceptions.ConnectionError), \
         patch("crypto_automation.time.sleep", return_value=None):
        result = pipeline.fetch_crypto_data_with_retry(retries=2, delay=0)

    assert result is None


# --- clean_raw_data ----------------------------------------------------------
def test_clean_raw_data_normalizes_and_uppercases():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)

    assert list(df["symbol"]) == ["BTC", "ETH"]
    # 2.5% -> 0.025 fraction
    assert df.loc[df["symbol"] == "BTC", "price_change_percentage_24h"].iloc[0] == pytest.approx(0.025)
    assert "snapshot_time" in df.columns


# --- validate_data -------------------------------------------------------------
def test_validate_data_passes_for_clean_data():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    pipeline.validate_data(df, expected_coin_count=2)  # should not raise


def test_validate_data_raises_on_missing_column():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON).drop(columns=["current_price"])
    with pytest.raises(ValueError, match="Missing expected column"):
        pipeline.validate_data(df)


def test_validate_data_raises_on_empty_dataframe():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON).iloc[0:0]
    with pytest.raises(ValueError, match="empty"):
        pipeline.validate_data(df)


def test_validate_data_raises_on_null_price():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df.loc[0, "current_price"] = None
    with pytest.raises(ValueError, match="null current_price"):
        pipeline.validate_data(df)


# --- load_and_merge_history: deduplication ------------------------------------
def test_merge_history_deduplicates_same_symbol_and_timestamp(tmp_path):
    df_new = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df_new["snapshot_time"] = "2026-08-01 12:00:00"

    output_file = tmp_path / "history.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_new.to_excel(writer, sheet_name="Crypto Market Timeline", index=False)

    # Merging the identical snapshot again should not duplicate rows
    df_updated = pipeline.load_and_merge_history(str(output_file), df_new)

    assert len(df_updated) == len(df_new)


def test_merge_history_appends_new_snapshot(tmp_path):
    df_first = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df_first["snapshot_time"] = "2026-08-01 12:00:00"

    output_file = tmp_path / "history.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_first.to_excel(writer, sheet_name="Crypto Market Timeline", index=False)

    df_second = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df_second["snapshot_time"] = "2026-08-01 13:00:00"

    df_updated = pipeline.load_and_merge_history(str(output_file), df_second)

    assert len(df_updated) == len(df_first) + len(df_second)


# --- backup_existing_file: retention -----------------------------------------
def test_backup_retention_keeps_only_max_backups(tmp_path):
    output_file = tmp_path / "history.xlsx"
    output_file.write_text("dummy content")
    backup_dir = tmp_path / "backups"

    # Simulate 12 prior backups already on disk
    backup_dir.mkdir()
    for i in range(12):
        (backup_dir / f"crypto_history_backup_2026080{i:01d}_000000.xlsx").write_text("x")

    pipeline.backup_existing_file(str(output_file), str(backup_dir), max_backups=10)

    remaining = [f for f in os.listdir(backup_dir) if f.startswith("crypto_history_backup_")]
    # 12 existing + 1 new = 13, retention keeps the most recent 10
    assert len(remaining) == 10


# --- is_snapshot_too_soon: throttling -----------------------------------------
def test_throttle_disabled_when_interval_is_zero(tmp_path):
    output_file = tmp_path / "history.xlsx"
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Crypto Market Timeline", index=False)

    assert pipeline.is_snapshot_too_soon(str(output_file), min_interval_minutes=0) is False


def test_throttle_skips_when_last_snapshot_is_recent(tmp_path):
    output_file = tmp_path / "history.xlsx"
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df["snapshot_time"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Crypto Market Timeline", index=False)

    assert pipeline.is_snapshot_too_soon(str(output_file), min_interval_minutes=60) is True


def test_throttle_allows_when_last_snapshot_is_old(tmp_path):
    output_file = tmp_path / "history.xlsx"
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    old_time = pd.Timestamp.now() - pd.Timedelta(hours=2)
    df["snapshot_time"] = old_time.strftime("%Y-%m-%d %H:%M:%S")
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Crypto Market Timeline", index=False)

    assert pipeline.is_snapshot_too_soon(str(output_file), min_interval_minutes=60) is False


def test_throttle_false_when_no_file_exists(tmp_path):
    output_file = tmp_path / "does_not_exist.xlsx"
    assert pipeline.is_snapshot_too_soon(str(output_file), min_interval_minutes=60) is False


# --- resolve_coin_ids: interactive ticker input --------------------------------
def test_resolve_coin_ids_from_space_separated_tickers():
    assert pipeline.resolve_coin_ids("btc eth sol") == "bitcoin,ethereum,solana"


def test_resolve_coin_ids_is_case_insensitive():
    assert pipeline.resolve_coin_ids("BTC Eth") == "bitcoin,ethereum"


def test_resolve_coin_ids_accepts_commas_too():
    assert pipeline.resolve_coin_ids("btc, eth, sol") == "bitcoin,ethereum,solana"


def test_resolve_coin_ids_passes_through_unknown_tokens_as_ids():
    # Not in TICKER_TO_COIN_ID -> assumed to already be a valid CoinGecko id
    assert pipeline.resolve_coin_ids("btc dogwifhat") == "bitcoin,dogwifhat"
