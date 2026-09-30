"""
Unit tests for crypto_automation.py and db.py.

Run with:
    pytest

No real network calls are made — the CoinPaprika API and Telegram are mocked.
"""

import os
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import crypto_automation as pipeline  # noqa: E402
import db  # noqa: E402


def make_ticker(coin_id, name, symbol, price, market_cap, volume_24h, percent_change_24h):
    """Build a CoinPaprika-shaped ticker object, as returned by
    GET /v1/tickers/{coin_id}?quotes=USD
    """
    return {
        "id": coin_id,
        "name": name,
        "symbol": symbol,
        "quotes": {
            "USD": {
                "price": price,
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "percent_change_24h": percent_change_24h,
            }
        },
    }


SAMPLE_RAW_JSON = [
    make_ticker("btc-bitcoin", "Bitcoin", "BTC", 65000.0, 1_280_000_000_000, 30_000_000_000, 2.5),
    make_ticker("eth-ethereum", "Ethereum", "ETH", 3500.0, 420_000_000_000, 15_000_000_000, -1.2),
]


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Every test gets its own throwaway SQLite file, so tests never touch
    a real crypto_history.db or interfere with each other.
    """
    monkeypatch.setattr(config, "DB_FILE", str(tmp_path / "test_history.db"))
    yield


# --- fetch_crypto_data_with_retry -------------------------------------------
def test_fetch_success_returns_json(monkeypatch):
    monkeypatch.setattr(config, "COIN_IDS", "btc-bitcoin,eth-ethereum")

    responses = []
    for ticker in SAMPLE_RAW_JSON:
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = ticker
        mock_response.raise_for_status.return_value = None
        responses.append(mock_response)

    with patch("crypto_automation.requests.get", side_effect=responses):
        result = pipeline.fetch_crypto_data_with_retry(retries=3, delay=0)

    assert result == SAMPLE_RAW_JSON


def test_fetch_retries_on_429_then_gives_up(monkeypatch):
    monkeypatch.setattr(config, "COIN_IDS", "btc-bitcoin")
    mock_response = Mock(status_code=429)

    with patch("crypto_automation.requests.get", return_value=mock_response) as mock_get, \
         patch("crypto_automation.time.sleep", return_value=None):
        result = pipeline.fetch_crypto_data_with_retry(retries=3, delay=0)

    assert result is None
    assert mock_get.call_count == 3


def test_fetch_returns_none_on_persistent_network_error(monkeypatch):
    monkeypatch.setattr(config, "COIN_IDS", "btc-bitcoin")

    with patch("crypto_automation.requests.get", side_effect=pipeline.requests.exceptions.ConnectionError), \
         patch("crypto_automation.time.sleep", return_value=None):
        result = pipeline.fetch_crypto_data_with_retry(retries=2, delay=0)

    assert result is None


def test_fetch_stops_after_first_coin_fails(monkeypatch):
    """If an earlier coin ultimately fails, later coins aren't even requested."""
    monkeypatch.setattr(config, "COIN_IDS", "btc-bitcoin,eth-ethereum")
    mock_response = Mock(status_code=500)
    mock_response.raise_for_status.side_effect = pipeline.requests.exceptions.HTTPError

    with patch("crypto_automation.requests.get", return_value=mock_response) as mock_get, \
         patch("crypto_automation.time.sleep", return_value=None):
        result = pipeline.fetch_crypto_data_with_retry(retries=1, delay=0)

    assert result is None
    assert mock_get.call_count == 1


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


# --- db.py: SQLite persistence layer --------------------------------------------
def test_db_insert_and_load_roundtrip():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    inserted = db.insert_snapshot(df)

    assert inserted == 2
    df_loaded = db.load_history()
    assert len(df_loaded) == 2
    assert set(df_loaded["symbol"]) == {"BTC", "ETH"}


def test_db_insert_ignores_exact_duplicates():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df["snapshot_time"] = "2026-08-01 12:00:00"

    first = db.insert_snapshot(df)
    second = db.insert_snapshot(df)  # identical (symbol, snapshot_time) pairs

    assert first == 2
    assert second == 0
    assert len(db.load_history()) == 2


def test_db_load_history_sorted_by_name_then_time():
    df1 = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df1["snapshot_time"] = "2026-08-01 12:00:00"
    db.insert_snapshot(df1)

    df2 = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df2["snapshot_time"] = "2026-08-01 13:00:00"
    db.insert_snapshot(df2)

    df_loaded = db.load_history()
    assert list(df_loaded["name"]) == ["Bitcoin", "Bitcoin", "Ethereum", "Ethereum"]
    assert list(df_loaded[df_loaded["name"] == "Bitcoin"]["snapshot_time"]) == [
        "2026-08-01 12:00:00", "2026-08-01 13:00:00",
    ]


# --- load_and_merge_history: dedup + growth via SQLite --------------------------
def test_merge_history_deduplicates_same_symbol_and_timestamp():
    df_new = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df_new["snapshot_time"] = "2026-08-01 12:00:00"

    pipeline.load_and_merge_history(df_new)
    df_updated = pipeline.load_and_merge_history(df_new)  # same snapshot again

    assert len(df_updated) == len(df_new)


def test_merge_history_appends_new_snapshot():
    df_first = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df_first["snapshot_time"] = "2026-08-01 12:00:00"
    pipeline.load_and_merge_history(df_first)

    df_second = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df_second["snapshot_time"] = "2026-08-01 13:00:00"
    df_updated = pipeline.load_and_merge_history(df_second)

    assert len(df_updated) == len(df_first) + len(df_second)


# --- backup_existing_file: retention -----------------------------------------
def test_backup_retention_keeps_only_max_backups(tmp_path):
    source_file = tmp_path / "history.db"
    source_file.write_text("dummy content")
    backup_dir = tmp_path / "backups"

    # Simulate 12 prior backups already on disk
    backup_dir.mkdir()
    for i in range(12):
        (backup_dir / f"crypto_history_backup_2026080{i:01d}_000000.db").write_text("x")

    pipeline.backup_existing_file(str(source_file), str(backup_dir), max_backups=10)

    remaining = [f for f in os.listdir(backup_dir) if f.startswith("crypto_history_backup_")]
    # 12 existing + 1 new = 13, retention keeps the most recent 10
    assert len(remaining) == 10


# --- is_snapshot_too_soon: throttling -----------------------------------------
def test_throttle_disabled_when_interval_is_zero():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    db.insert_snapshot(df)

    assert pipeline.is_snapshot_too_soon(min_interval_minutes=0) is False


def test_throttle_skips_when_last_snapshot_is_recent():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    df["snapshot_time"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    db.insert_snapshot(df)

    assert pipeline.is_snapshot_too_soon(min_interval_minutes=60) is True


def test_throttle_allows_when_last_snapshot_is_old():
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    old_time = pd.Timestamp.now() - pd.Timedelta(hours=2)
    df["snapshot_time"] = old_time.strftime("%Y-%m-%d %H:%M:%S")
    db.insert_snapshot(df)

    assert pipeline.is_snapshot_too_soon(min_interval_minutes=60) is False


def test_throttle_false_when_no_db_exists():
    assert pipeline.is_snapshot_too_soon(min_interval_minutes=60) is False


# --- resolve_coin_ids: interactive ticker input --------------------------------
def test_resolve_coin_ids_from_space_separated_tickers():
    assert pipeline.resolve_coin_ids("btc eth sol") == "btc-bitcoin,eth-ethereum,sol-solana"


def test_resolve_coin_ids_is_case_insensitive():
    assert pipeline.resolve_coin_ids("BTC Eth") == "btc-bitcoin,eth-ethereum"


def test_resolve_coin_ids_accepts_commas_too():
    assert pipeline.resolve_coin_ids("btc, eth, sol") == "btc-bitcoin,eth-ethereum,sol-solana"


def test_resolve_coin_ids_passes_through_unknown_tokens_as_ids():
    # Not in TICKER_TO_COIN_ID -> assumed to already be a valid CoinPaprika id
    assert pipeline.resolve_coin_ids("btc dogwifhat") == "btc-bitcoin,dogwifhat"


# --- check_price_alerts / send_telegram_alert: Telegram integration -------------
def test_alerts_noop_when_telegram_not_configured(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(config, "TELEGRAM_CHAT_ID", "")

    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    with patch("crypto_automation.requests.post") as mock_post:
        pipeline.check_price_alerts(df)

    mock_post.assert_not_called()


def test_alerts_sent_when_change_exceeds_threshold(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setattr(config, "TELEGRAM_CHAT_ID", "fake-chat-id")
    monkeypatch.setattr(config, "ALERT_THRESHOLD_PERCENT", 2.0)

    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)  # BTC +2.5%, ETH -1.2%

    mock_response = Mock(status_code=200)
    with patch("crypto_automation.requests.post", return_value=mock_response) as mock_post:
        pipeline.check_price_alerts(df)

    # Only BTC crosses the 2.0% threshold; ETH's 1.2% doesn't
    assert mock_post.call_count == 1
    sent_text = mock_post.call_args.kwargs["data"]["text"]
    assert "Bitcoin" in sent_text


def test_alerts_not_sent_when_below_threshold(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setattr(config, "TELEGRAM_CHAT_ID", "fake-chat-id")
    monkeypatch.setattr(config, "ALERT_THRESHOLD_PERCENT", 10.0)  # neither coin crosses this

    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    with patch("crypto_automation.requests.post") as mock_post:
        pipeline.check_price_alerts(df)

    mock_post.assert_not_called()


# --- build_excel_report: integration ------------------------------------------
def test_build_excel_report_creates_dashboard_and_timeline_sheets(tmp_path):
    df = pipeline.clean_raw_data(SAMPLE_RAW_JSON)
    output_file = tmp_path / "report.xlsx"

    pipeline.build_excel_report(df, str(output_file))

    assert output_file.exists()
    import openpyxl
    wb = openpyxl.load_workbook(output_file)
    assert "Dashboard" in wb.sheetnames
    assert "Crypto Market Timeline" in wb.sheetnames
    assert "ChartData" in wb.sheetnames
    assert wb["ChartData"].sheet_state == "hidden"
    assert len(wb["Dashboard"]._charts) == 1


# --- main(): full pipeline orchestration ----------------------------------------
def test_main_end_to_end_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "COIN_IDS", "btc-bitcoin,eth-ethereum")
    monkeypatch.setattr(config, "OUTPUT_FILE", str(tmp_path / "out.xlsx"))
    monkeypatch.setattr(config, "BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setattr(config, "LOG_FILE", str(tmp_path / "pipeline.log"))

    responses = []
    for ticker in SAMPLE_RAW_JSON:
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = ticker
        mock_response.raise_for_status.return_value = None
        responses.append(mock_response)

    with patch("crypto_automation.requests.get", side_effect=responses):
        exit_code = pipeline.main()

    assert exit_code == 0
    assert os.path.exists(config.OUTPUT_FILE)
    assert os.path.exists(config.DB_FILE)
    assert len(db.load_history()) == 2


def test_main_returns_1_on_fetch_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "COIN_IDS", "btc-bitcoin")
    monkeypatch.setattr(config, "LOG_FILE", str(tmp_path / "pipeline.log"))

    with patch("crypto_automation.requests.get", side_effect=pipeline.requests.exceptions.ConnectionError), \
         patch("crypto_automation.time.sleep", return_value=None):
        exit_code = pipeline.main()

    assert exit_code == 1


def test_main_returns_1_on_validation_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "COIN_IDS", "btc-bitcoin")
    monkeypatch.setattr(config, "LOG_FILE", str(tmp_path / "pipeline.log"))

    bad_ticker = make_ticker("btc-bitcoin", "Bitcoin", "BTC", None, 1_280_000_000_000, 30_000_000_000, 2.5)
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = bad_ticker
    mock_response.raise_for_status.return_value = None

    with patch("crypto_automation.requests.get", return_value=mock_response):
        exit_code = pipeline.main()

    assert exit_code == 1