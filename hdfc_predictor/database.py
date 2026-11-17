"""
SQLite Database Layer for HDFC Predictor.
Stores daily predictions, actual verified market outcomes, and learning history.
"""
import sqlite3
import json
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
