"""
SQLite Database Layer for HDFC Predictor.
Stores daily predictions, actual verified market outcomes, and learning history.
"""
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from hdfc_predictor.config import settings


def get_db_connection():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        date TEXT NOT NULL,
        symbol TEXT NOT NULL,
        price_at_signal REAL NOT NULL,
        day_open REAL,
        day_high REAL,
        day_low REAL,
        signal_action TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        sentiment_score REAL NOT NULL,
        rsi_14 REAL,
        macd_val REAL,
        macd_signal REAL,
        stop_loss REAL,
        target_price REAL,
        headline_sample TEXT,
        reasoning TEXT,
        features_json TEXT,
        status TEXT DEFAULT 'PENDING_EVALUATION'
    )
    """)
    
    # 2. Outcomes Table (Reconciliation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS outcomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_id INTEGER UNIQUE,
        target_date TEXT NOT NULL,
        actual_close_price REAL,
        actual_next_open REAL,
        actual_next_close REAL,
        actual_change_pct REAL,
        prediction_correct INTEGER,
        simulated_pnl_pct REAL,
        verified_at TEXT NOT NULL,
        FOREIGN KEY (prediction_id) REFERENCES predictions(id)
    )
    """)
    
    # 3. Learning History / Metrics Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evaluated_at TEXT NOT NULL,
        total_samples INTEGER,
        overall_accuracy REAL,
        rolling_7d_accuracy REAL,
        rolling_30d_accuracy REAL,
        total_pnl_pct REAL,
        profit_factor REAL,
        calibrated_buy_threshold REAL,
        calibrated_sell_threshold REAL,
        notes TEXT
    )
    """)
    
    # 4. News Archive Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fetched_at TEXT NOT NULL,
        published_date TEXT,
        source TEXT,
        title TEXT UNIQUE,
        description TEXT,
        url TEXT,
        sentiment_score REAL,
        sentiment_label TEXT
    )
    """)

    # 5. Raw Observations (Point-in-Time Historical Store with Source Attribution)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric TEXT NOT NULL,
        value REAL NOT NULL,
        source TEXT NOT NULL,
        as_of_date TEXT NOT NULL,
        filing_timestamp TEXT,
        entity_scope TEXT NOT NULL,
        revision_no INTEGER DEFAULT 0,
        fetched_at TEXT NOT NULL,
        is_verified INTEGER DEFAULT 0
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_obs_metric_date ON raw_observations (metric, entity_scope, as_of_date)")

    # 6. Corporate Actions Table (Splits, Bonuses, Mergers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS corporate_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        action_type TEXT NOT NULL,
        ex_date TEXT NOT NULL,
        record_date TEXT,
        ratio_from REAL,
        ratio_to REAL,
        split_factor REAL NOT NULL,
        notes TEXT
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_corp_act_sym_date ON corporate_actions (symbol, ex_date)")

    # 7. Data Quality Audit Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data_quality_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        check_type TEXT NOT NULL,
        symbol TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        severity TEXT NOT NULL
    )
    """)

    # 8. Unified Immutable Decisions Table with Cryptographic Hash-Chain
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        data_vintage TEXT NOT NULL,
        model_version TEXT NOT NULL,
        threshold_version TEXT NOT NULL,
        feature_vector_json TEXT NOT NULL,
        prompts_used_json TEXT,
        forecast_distributions_json TEXT NOT NULL,
        regime_probabilities_json TEXT NOT NULL,
        tactical_levels_json TEXT NOT NULL,
        tranche_pct REAL NOT NULL,
        exact_shares INTEGER NOT NULL,
        exact_cash_amount REAL NOT NULL,
        abstain_flag INTEGER NOT NULL,
        abstain_reasons_json TEXT,
        decision_action TEXT NOT NULL,
        code_commit_hash TEXT NOT NULL,
        prev_row_hash TEXT NOT NULL,
        row_hash TEXT NOT NULL
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_ts ON decisions (timestamp)")

    # Seed Default Corporate Actions for HDFC Bank if empty
    cursor.execute("SELECT COUNT(*) FROM corporate_actions WHERE symbol = 'HDFCBANK.NS'")
    if cursor.fetchone()[0] == 0:
        seed_actions = [
            ('HDFCBANK.NS', 'SPLIT', '2011-07-14', '2011-07-16', 1.0, 5.0, 5.0, 'Stock split 1:5 (Face Value 10 to 2)'),
            ('HDFCBANK.NS', 'SPLIT', '2019-09-19', '2019-09-20', 1.0, 2.0, 2.0, 'Stock split 1:2 (Face Value 2 to 1)'),
            ('HDFCBANK.NS', 'MERGER', '2023-07-01', '2023-07-13', 25.0, 42.0, 1.68, 'HDFC Ltd merger: 42 HDFC Bank shares per 25 HDFC Ltd shares')
        ]
        cursor.executemany("""
        INSERT INTO corporate_actions (symbol, action_type, ex_date, record_date, ratio_from, ratio_to, split_factor, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_actions)
    
    conn.commit()
    conn.close()


def log_raw_observation(
    metric: str,
    value: float,
    source: str,
    as_of_date: str,
    entity_scope: str = "HDFCBANK_STANDALONE",
    filing_timestamp: Optional[str] = None,
    revision_no: int = 0,
    is_verified: bool = False
) -> int:
    """Inserts a point-in-time observation with data lineage metadata."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO raw_observations (
        metric, value, source, as_of_date, filing_timestamp,
        entity_scope, revision_no, fetched_at, is_verified
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metric, float(value), source, as_of_date, filing_timestamp,
        entity_scope, revision_no, now_str, 1 if is_verified else 0
    ))
    obs_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return obs_id


def get_point_in_time_observation(
    metric: str,
    entity_scope: str = "HDFCBANK_STANDALONE",
    as_of_date: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent observation known as of a specific date (no look-ahead).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if as_of_date:
        cursor.execute("""
        SELECT * FROM raw_observations
        WHERE metric = ? AND entity_scope = ? AND as_of_date <= ?
        ORDER BY as_of_date DESC, revision_no DESC
        LIMIT 1
        """, (metric, entity_scope, as_of_date))
    else:
        cursor.execute("""
        SELECT * FROM raw_observations
        WHERE metric = ? AND entity_scope = ?
        ORDER BY as_of_date DESC, revision_no DESC
        LIMIT 1
        """, (metric, entity_scope))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def log_data_quality(
    check_type: str,
    symbol: str,
    status: str,
    details: str,
    severity: str = "INFO"
) -> int:
    """Records data quality checks, schema alerts, or outlier rejections."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO data_quality_log (timestamp, check_type, symbol, status, details, severity)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (now_str, check_type, symbol, status, details, severity))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_corporate_actions(symbol: str) -> List[Dict[str, Any]]:
    """Fetches all corporate actions for symbol ordered by date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM corporate_actions WHERE symbol = ? ORDER BY ex_date ASC
    """, (symbol,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
    
    conn.commit()
    conn.close()


def save_prediction(record: Dict[str, Any]) -> int:
    """Inserts a new daily 2:00 PM prediction."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO predictions (
        timestamp, date, symbol, price_at_signal, day_open, day_high, day_low,
        signal_action, confidence_score, sentiment_score, rsi_14, macd_val,
        macd_signal, stop_loss, target_price, headline_sample, reasoning,
        features_json, status
    ) VALUES (
        :timestamp, :date, :symbol, :price_at_signal, :day_open, :day_high, :day_low,
        :signal_action, :confidence_score, :sentiment_score, :rsi_14, :macd_val,
        :macd_signal, :stop_loss, :target_price, :headline_sample, :reasoning,
        :features_json, 'PENDING_EVALUATION'
    )
    """, record)
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id


def get_pending_predictions() -> List[Dict[str, Any]]:
    """Returns predictions waiting for outcome verification."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM predictions 
    WHERE status = 'PENDING_EVALUATION'
    ORDER BY date ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def record_outcome(prediction_id: int, outcome_data: Dict[str, Any]):
    """Records the verified market outcome and marks prediction verified."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO outcomes (
        prediction_id, target_date, actual_close_price, actual_next_open,
        actual_next_close, actual_change_pct, prediction_correct,
        simulated_pnl_pct, verified_at
    ) VALUES (
        :prediction_id, :target_date, :actual_close_price, :actual_next_open,
        :actual_next_close, :actual_change_pct, :prediction_correct,
        :simulated_pnl_pct, :verified_at
    )
    """, {**outcome_data, "prediction_id": prediction_id})
    
    cursor.execute("""
    UPDATE predictions SET status = 'VERIFIED' WHERE id = ?
    """, (prediction_id,))
    
    conn.commit()
    conn.close()


def save_learning_checkpoint(stats: Dict[str, Any]):
    """Saves learning progression and threshold calibration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO learning_history (
        evaluated_at, total_samples, overall_accuracy, rolling_7d_accuracy,
        rolling_30d_accuracy, total_pnl_pct, profit_factor,
        calibrated_buy_threshold, calibrated_sell_threshold, notes
    ) VALUES (
        :evaluated_at, :total_samples, :overall_accuracy, :rolling_7d_accuracy,
        :rolling_30d_accuracy, :total_pnl_pct, :profit_factor,
        :calibrated_buy_threshold, :calibrated_sell_threshold, :notes
    )
    """, stats)
    conn.commit()
    conn.close()


def get_recent_predictions(limit: int = 15) -> List[Dict[str, Any]]:
    """Fetches recent predictions with their verified outcomes if available."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        p.*, 
        o.actual_next_close,
        o.actual_change_pct,
        o.prediction_correct,
        o.simulated_pnl_pct
    FROM predictions p
    LEFT JOIN outcomes o ON p.id = o.prediction_id
    ORDER BY p.id DESC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_learning_progress() -> List[Dict[str, Any]]:
    """Returns chronological learning progression."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM learning_history ORDER BY id ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


GENESIS_HASH = "0" * 64


def calculate_decision_row_hash(payload: Dict[str, Any], prev_hash: str) -> str:
    """Calculates deterministic SHA-256 cryptographic hash over decision fields."""
    serialized = (
        f"{prev_hash}|"
        f"{payload.get('timestamp')}|"
        f"{payload.get('data_vintage')}|"
        f"{payload.get('model_version')}|"
        f"{payload.get('threshold_version')}|"
        f"{payload.get('feature_vector_json')}|"
        f"{payload.get('forecast_distributions_json')}|"
        f"{payload.get('regime_probabilities_json')}|"
        f"{payload.get('tactical_levels_json')}|"
        f"{payload.get('tranche_pct')}|"
        f"{payload.get('exact_shares')}|"
        f"{payload.get('exact_cash_amount')}|"
        f"{payload.get('abstain_flag')}|"
        f"{payload.get('decision_action')}|"
        f"{payload.get('code_commit_hash')}"
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def insert_immutable_decision(
    timestamp: str,
    data_vintage: str,
    model_version: str,
    threshold_version: str,
    feature_vector: Dict[str, Any],
    forecast_distributions: Dict[str, Any],
    regime_probabilities: Dict[str, Any],
    tactical_levels: Dict[str, Any],
    tranche_pct: float,
    exact_shares: int,
    exact_cash_amount: float,
    abstain_flag: int,
    decision_action: str,
    code_commit_hash: str,
    prompts_used: Optional[List[str]] = None,
    abstain_reasons: Optional[List[str]] = None
) -> str:
    """
    Inserts a row into the immutable decisions ledger with cryptographic SHA-256 hash chaining.
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the hash of the latest row
    cursor.execute("SELECT row_hash FROM decisions ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    prev_row_hash = row["row_hash"] if row else GENESIS_HASH

    feat_json = json.dumps(feature_vector, sort_keys=True)
    dist_json = json.dumps(forecast_distributions, sort_keys=True)
    reg_json = json.dumps(regime_probabilities, sort_keys=True)
    tact_json = json.dumps(tactical_levels, sort_keys=True)
    prompts_json = json.dumps(prompts_used or [], sort_keys=True)
    reasons_json = json.dumps(abstain_reasons or [], sort_keys=True)

    payload = {
        "timestamp": timestamp,
        "data_vintage": data_vintage,
        "model_version": model_version,
        "threshold_version": threshold_version,
        "feature_vector_json": feat_json,
        "forecast_distributions_json": dist_json,
        "regime_probabilities_json": reg_json,
        "tactical_levels_json": tact_json,
        "tranche_pct": tranche_pct,
        "exact_shares": exact_shares,
        "exact_cash_amount": exact_cash_amount,
        "abstain_flag": abstain_flag,
        "decision_action": decision_action,
        "code_commit_hash": code_commit_hash
    }

    current_row_hash = calculate_decision_row_hash(payload, prev_row_hash)

    cursor.execute("""
    INSERT INTO decisions (
        timestamp, data_vintage, model_version, threshold_version,
        feature_vector_json, prompts_used_json, forecast_distributions_json,
        regime_probabilities_json, tactical_levels_json, tranche_pct,
        exact_shares, exact_cash_amount, abstain_flag, abstain_reasons_json,
        decision_action, code_commit_hash, prev_row_hash, row_hash
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        timestamp, data_vintage, model_version, threshold_version,
        feat_json, prompts_json, dist_json,
        reg_json, tact_json, tranche_pct,
        exact_shares, exact_cash_amount, abstain_flag, reasons_json,
        decision_action, code_commit_hash, prev_row_hash, current_row_hash
    ))
    conn.commit()
    conn.close()
    return current_row_hash


def verify_decision_chain_integrity() -> Tuple[bool, List[str]]:
    """
    Verifies cryptographic hash-chain integrity across all historical decisions.
    Returns (is_valid, list_of_errors).
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM decisions ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return True, ["No decisions recorded yet; empty chain is valid."]

    expected_prev_hash = GENESIS_HASH
    errors = []

    for idx, r in enumerate(rows):
        row_dict = dict(r)
        actual_prev = row_dict["prev_row_hash"]
        actual_hash = row_dict["row_hash"]

        if actual_prev != expected_prev_hash:
            errors.append(f"Row ID {row_dict['id']}: prev_row_hash mismatch! Expected {expected_prev_hash[:12]}..., got {actual_prev[:12]}...")

        # Re-compute hash
        recalc_hash = calculate_decision_row_hash(row_dict, actual_prev)
        if recalc_hash != actual_hash:
            errors.append(f"Row ID {row_dict['id']}: row_hash tampered or mismatch! Recalculated {recalc_hash[:12]}... != Stored {actual_hash[:12]}...")

        expected_prev_hash = actual_hash

    return (len(errors) == 0), errors


def get_latest_decision() -> Optional[Dict[str, Any]]:
    """Retrieves the most recent decision record."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

