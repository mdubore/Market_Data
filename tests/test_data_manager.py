"""
Unit tests for DataManager module
"""

import pytest
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from src.data_manager import DataManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database with test data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE market_data (
            id INTEGER PRIMARY KEY,
            ticker TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER,
            UNIQUE(ticker, date)
        )
    """)
    
    # Insert sample data
    base_date = datetime(2023, 1, 1)
    for i in range(100):
        date = (base_date + timedelta(days=i)).date()
        cursor.execute("""
            INSERT INTO market_data 
            (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'AAPL',
            date,
            100.0 + i * 0.1,
            101.0 + i * 0.1,
            99.0 + i * 0.1,
            100.5 + i * 0.1,
            1000000
        ))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


class TestDataManager:
    """Test DataManager class."""
    
    def test_initialization(self, temp_db):
        """Test DataManager initialization."""
        dm = DataManager(temp_db)
        assert dm.db_path == temp_db
        assert dm._cache == {}
    
    def test_initialization_missing_db(self):
        """Test DataManager initialization with missing database."""
        with pytest.raises(FileNotFoundError):
            DataManager("nonexistent_database.db")
    
    def test_get_available_tickers(self, temp_db):
        """Test getting available tickers."""
        dm = DataManager(temp_db)
        tickers = dm.get_available_tickers()
        
        assert isinstance(tickers, list)
        assert 'AAPL' in tickers
        assert len(tickers) >= 1
    
    def test_get_ohlcv_data(self, temp_db):
        """Test retrieving OHLCV data."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        assert df.index.name == 'date'
    
    def test_get_ohlcv_data_invalid_ticker(self, temp_db):
        """Test retrieving OHLCV data for invalid ticker."""
        dm = DataManager(temp_db)
        
        with pytest.raises(ValueError):
            dm.get_ohlcv_data('INVALID')
    
    def test_aggregate_ohlcv_daily(self, temp_db):
        """Test daily aggregation (should return unchanged)."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        df_agg = dm.aggregate_ohlcv(df, 'daily')
        
        assert len(df_agg) == len(df)
        assert df_agg.equals(df)
    
    def test_aggregate_ohlcv_weekly(self, temp_db):
        """Test weekly aggregation."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        df_agg = dm.aggregate_ohlcv(df, 'weekly')
        
        assert len(df_agg) < len(df)
        assert all(col in df_agg.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    
    def test_aggregate_ohlcv_monthly(self, temp_db):
        """Test monthly aggregation."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        df_agg = dm.aggregate_ohlcv(df, 'monthly')
        
        assert len(df_agg) <= len(df)
        assert all(col in df_agg.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    
    def test_aggregate_ohlcv_invalid_timeframe(self, temp_db):
        """Test aggregation with invalid timeframe."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        
        with pytest.raises(ValueError):
            dm.aggregate_ohlcv(df, 'invalid')
    
    def test_get_date_range(self, temp_db):
        """Test getting date range."""
        dm = DataManager(temp_db)
        start, end = dm.get_date_range('AAPL')
        
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start <= end
    
    def test_get_ticker_info(self, temp_db):
        """Test getting ticker information."""
        dm = DataManager(temp_db)
        info = dm.get_ticker_info('AAPL')
        
        assert info['ticker'] == 'AAPL'
        assert 'start_date' in info
        assert 'end_date' in info
        assert 'record_count' in info
        assert 'current_price' in info
        assert 'highest_price' in info
        assert 'lowest_price' in info
        assert 'average_volume' in info
    
    def test_validate_data_valid(self, temp_db):
        """Test data validation with valid data."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        
        is_valid, errors = dm.validate_data(df)
        assert is_valid
        assert errors == []
    
    def test_validate_data_empty(self):
        """Test data validation with empty DataFrame."""
        dm = DataManager.__new__(DataManager)
        df = pd.DataFrame()
        
        is_valid, errors = dm.validate_data(df)
        assert not is_valid
        assert 'empty' in errors[0].lower()
    
    def test_validate_data_missing_columns(self):
        """Test data validation with missing columns."""
        dm = DataManager.__new__(DataManager)
        df = pd.DataFrame({'open': [100], 'close': [101]})
        
        is_valid, errors = dm.validate_data(df)
        assert not is_valid
    
    def test_cache_functionality(self, temp_db):
        """Test caching of OHLCV data."""
        dm = DataManager(temp_db)
        
        # First call should cache the data
        df1 = dm.get_ohlcv_data('AAPL')
        assert f"ohlcv_AAPL" in dm._cache
        
        # Second call should use cache
        df2 = dm.get_ohlcv_data('AAPL')
        assert df1.equals(df2)
    
    def test_clear_cache(self, temp_db):
        """Test clearing cache."""
        dm = DataManager(temp_db)
        
        # Cache some data
        dm.get_ohlcv_data('AAPL')
        assert len(dm._cache) > 0
        
        # Clear cache
        dm.clear_cache()
        assert len(dm._cache) == 0


class TestDataAggregation:
    """Test data aggregation functionality."""
    
    def test_aggregation_preserves_ohlc_properties(self, temp_db):
        """Test that aggregation maintains OHLC properties."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        df_weekly = dm.aggregate_ohlcv(df, 'weekly')
        
        # High should be >= Low
        assert (df_weekly['high'] >= df_weekly['low']).all()
        
        # Open and Close should be within High and Low
        assert (df_weekly['open'] <= df_weekly['high']).all()
        assert (df_weekly['open'] >= df_weekly['low']).all()
        assert (df_weekly['close'] <= df_weekly['high']).all()
        assert (df_weekly['close'] >= df_weekly['low']).all()
    
    def test_aggregation_volume_sums(self, temp_db):
        """Test that volume is summed in aggregation."""
        dm = DataManager(temp_db)
        df = dm.get_ohlcv_data('AAPL')
        
        df_weekly = dm.aggregate_ohlcv(df, 'weekly')
        
        # Volume should be positive
        assert (df_weekly['volume'] > 0).all()
        
        # Weekly volume should be >= daily volume
        assert (df_weekly['volume'] >= df['volume'].min()).all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
