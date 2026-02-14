#!/usr/bin/env python3
"""
Financial Market Data Retriever & Local Database Manager
=========================================================
Retrieves OHLC prices, adjusted close, and volume for configured tickers
using yfinance, stores them in a local SQLite database, and keeps it
updated on a daily cycle.
"""

import sqlite3
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("yfinance is required. Install with: pip install yfinance")

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required. Install with: pip install pyyaml")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONFIG_PATH = Path("market_data_config.yaml")
CONFIG: dict = {}

def load_config(config_path: Path) -> dict:
    """Load configuration from a YAML file."""
    if not config_path.exists():
        raise SystemExit(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise SystemExit("Configuration file is empty")
        
        log.info("Configuration loaded from %s", config_path)
        return config
    except yaml.YAMLError as e:
        raise SystemExit(f"Failed to parse YAML configuration: {e}")
    except Exception as e:
        raise SystemExit(f"Error reading configuration file: {e}")


def get_config_value(key: str, default=None):
    """Get a configuration value using dot notation (e.g., 'database.path')."""
    keys = key.split(".")
    value = CONFIG
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                return default
        else:
            return default
    return value

# Initialize logging first (will be reconfigured after config loads)
log = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging based on loaded configuration."""
    log_level = get_config_value("logging.level", "INFO")
    log_format = get_config_value("logging.format", "%(asctime)s [%(levelname)s] %(message)s")
    log_date_format = get_config_value("logging.date_format", "%Y-%m-%d %H:%M:%S")
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=log_format,
        datefmt=log_date_format,
    )


# ---------------------------------------------------------------------------
# Ticker parsing
# ---------------------------------------------------------------------------
def parse_tickers(tickers_list: list[str]) -> list[str]:
    """Validate and return ticker symbols from configuration."""
    if not tickers_list:
        log.warning("No tickers found in configuration")
        return []
    
    # Ensure all tickers are uppercase and stripped of whitespace
    validated_tickers = [t.strip().upper() for t in tickers_list if t and isinstance(t, str)]
    log.info("Loaded tickers: %s", validated_tickers)
    return validated_tickers


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def init_db(db_path: Path) -> sqlite3.Connection:
    """Create (or open) the SQLite database and ensure the schema exists."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ohlc_data (
            ticker      TEXT    NOT NULL,
            date        TEXT    NOT NULL,   -- ISO-8601 date string (YYYY-MM-DD)
            open        REAL,
            high        REAL,
            low         REAL,
            close       REAL,
            adj_close   REAL,
            volume      INTEGER,
            PRIMARY KEY (ticker, date)
        );
    """)
    # Indexes for common query patterns
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ohlc_ticker ON ohlc_data(ticker);
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ohlc_date ON ohlc_data(date);
    """)
    conn.commit()
    log.info("Database initialized at %s", db_path)
    return conn


def get_last_date(conn: sqlite3.Connection, ticker: str) -> str | None:
    """Return the most recent date string for a ticker, or None if no data."""
    row = conn.execute(
        "SELECT MAX(date) FROM ohlc_data WHERE ticker = ?", (ticker,)
    ).fetchone()
    return row[0] if row and row[0] else None


def insert_rows(conn: sqlite3.Connection, ticker: str, df) -> int:
    """Insert a yfinance DataFrame into the database. Returns rows inserted."""
    import pandas as pd
    
    if df is None or df.empty:
        return 0

    rows = []
    for idx, row in df.iterrows():
        date_str = idx.strftime("%Y-%m-%d")
        
        # Use pd.notna() for reliable NaN checking on pandas Series
        # row.get() doesn't work reliably on pandas Series objects
        open_val = round(float(row["Open"]), 6) if pd.notna(row["Open"]) else None
        high_val = round(float(row["High"]), 6) if pd.notna(row["High"]) else None
        low_val = round(float(row["Low"]), 6) if pd.notna(row["Low"]) else None
        close_val = round(float(row["Close"]), 6) if pd.notna(row["Close"]) else None
        
        # Handle Adj Close - fall back to Close if not available
        adj_close = row["Adj Close"] if "Adj Close" in row.index else row["Close"]
        adj_close_val = round(float(adj_close), 6) if pd.notna(adj_close) else None
        
        volume_val = int(row["Volume"]) if pd.notna(row["Volume"]) else None
        
        rows.append((
            ticker,
            date_str,
            open_val,
            high_val,
            low_val,
            close_val,
            adj_close_val,
            volume_val,
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO ohlc_data
            (ticker, date, open, high, low, close, adj_close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------
def fetch_full_history(conn: sqlite3.Connection, ticker: str) -> None:
    """Download up to HISTORY_YEARS of daily data for a ticker."""
    start = (datetime.now() - timedelta(days=HISTORY_YEARS * 365)).strftime("%Y-%m-%d")
    log.info("Fetching full history for %s from %s", ticker, start)
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(start=start, interval="1d", auto_adjust=False)
        count = insert_rows(conn, ticker, df)
        log.info("Inserted %d rows for %s", count, ticker)
    except Exception as exc:
        log.error("Failed to fetch history for %s: %s", ticker, exc)


def fetch_update(conn: sqlite3.Connection, ticker: str) -> None:
    """Download only new data since the last recorded date for a ticker."""
    last_date = get_last_date(conn, ticker)
    if last_date is None:
        # No data yet – fall back to full history
        fetch_full_history(conn, ticker)
        return

    # Start one day after the last recorded date to avoid duplicates
    start = (datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    if start > today:
        log.info("Ticker %s is already up-to-date (last: %s)", ticker, last_date)
        return

    log.info("Updating %s from %s to %s", ticker, start, today)
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(start=start, interval="1d", auto_adjust=False)
        count = insert_rows(conn, ticker, df)
        log.info("Appended %d new rows for %s", count, ticker)
    except Exception as exc:
        log.error("Failed to update %s: %s", ticker, exc)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run_update_cycle(conn: sqlite3.Connection, tickers: list[str], throttle_seconds: int) -> None:
    """Run one full update cycle across all tickers."""
    for i, ticker in enumerate(tickers):
        last = get_last_date(conn, ticker)
        if last is None:
            log.info("No existing data for %s – pulling full history", ticker)
            fetch_full_history(conn, ticker)
        else:
            fetch_update(conn, ticker)

        # Throttle between requests to avoid rate limiting
        if throttle_seconds > 0 and i < len(tickers) - 1:
            time.sleep(throttle_seconds)


def main() -> None:
    global CONFIG
    
    # Load configuration from YAML file
    CONFIG = load_config(CONFIG_PATH)
    setup_logging()
    
    # Extract configuration values
    tickers = parse_tickers(get_config_value("tickers", []))
    if not tickers:
        log.error("No tickers found in configuration. Exiting.")
        return
    
    db_path = Path(get_config_value("database.path", "market_data.db"))
    history_years = get_config_value("database.history_years", 15)
    sleep_seconds = get_config_value("schedule.update_interval_seconds", 86400)
    throttle_seconds = get_config_value("schedule.throttle_between_requests", 0)
    
    # Update global variables used in fetch functions
    globals()["HISTORY_YEARS"] = history_years
    
    db_exists = db_path.exists()
    conn = init_db(db_path)
    
    try:
        if not db_exists:
            log.info("Fresh database – performing initial historical load")
        
        # First cycle always runs immediately
        log.info("Starting initial update cycle with %d tickers", len(tickers))
        run_update_cycle(conn, tickers, throttle_seconds)
        
        # Continuous daily loop
        log.info("Entering daily update loop (updating every %d seconds)", sleep_seconds)
        while True:
            log.info("Sleeping until next cycle…")
            time.sleep(sleep_seconds)
            log.info("Waking up for scheduled update")
            run_update_cycle(conn, tickers, throttle_seconds)
    except KeyboardInterrupt:
        log.info("Received keyboard interrupt, shutting down gracefully")
    finally:
        conn.close()
        log.info("Database connection closed")


if __name__ == "__main__":
    main()
