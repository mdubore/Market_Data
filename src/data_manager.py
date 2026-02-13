"""
Data Manager Module

Handles all database operations, data retrieval, and time scale aggregation
for the interactive charting application.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class DataManager:
    """
    Manages data operations including database access, OHLC retrieval,
    and time scale aggregation.
    """
    
    def __init__(self, db_path: str = "market_data.db"):
        """
        Initialize the DataManager.
        
        Args:
            db_path (str): Path to the SQLite database file
        
        Raises:
            FileNotFoundError: If database file doesn't exist
        """
        self.db_path = db_path
        
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        self._cache = {}
        self._cache_ttl = 3600  # Cache TTL in seconds
    
    def get_available_tickers(self) -> List[str]:
        """
        Retrieve all available tickers from the database.
        
        Returns:
            List[str]: List of ticker symbols
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get distinct tickers from market_data table
            cursor.execute("SELECT DISTINCT ticker FROM ohlc_data ORDER BY ticker")
            tickers = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tickers
        
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
    
    def get_ohlcv_data(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve OHLCV data for a specific ticker.
        
        Args:
            ticker (str): Ticker symbol
        
        Returns:
            pd.DataFrame: DataFrame with columns [date, open, high, low, close, volume]
        
        Raises:
            ValueError: If ticker not found
            RuntimeError: If database error occurs
        """
        cache_key = f"ohlcv_{ticker}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT date, open, high, low, close, volume
            FROM ohlc_data
            WHERE ticker = ?
            ORDER BY date ASC
            """
            
            df = pd.read_sql_query(
                query,
                conn,
                params=(ticker,),
                parse_dates=['date']
            )
            
            conn.close()
            
            if df.empty:
                raise ValueError(f"No data found for ticker: {ticker}")
            
            # Set date as index
            df.set_index('date', inplace=True)
            
            # Cache the result
            self._cache[cache_key] = df.copy()
            
            return df
        
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
    
    def aggregate_ohlcv(
        self,
        df: pd.DataFrame,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Aggregate OHLCV data to different timeframes.
        
        Args:
            df (pd.DataFrame): Daily OHLCV DataFrame with datetime index
            timeframe (str): 'daily', 'weekly', or 'monthly'
        
        Returns:
            pd.DataFrame: Aggregated OHLCV DataFrame
        
        Raises:
            ValueError: If invalid timeframe specified
        """
        if timeframe.lower() == 'daily':
            return df.copy()
        
        df_copy = df.copy()
        
        if timeframe.lower() == 'weekly':
            # Aggregate to weeks (Friday close)
            agg_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            
            df_agg = df_copy.resample('W-FRI').agg(agg_dict)
        
        elif timeframe.lower() == 'monthly':
            # Aggregate to months (last day of month)
            agg_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            
            df_agg = df_copy.resample('M').agg(agg_dict)
        
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}. "
                           "Must be 'daily', 'weekly', or 'monthly'")
        
        # Remove rows with NaN values from aggregation
        df_agg = df_agg.dropna()
        
        return df_agg
    
    def get_date_range(self, ticker: str) -> Tuple[datetime, datetime]:
        """
        Get the date range of available data for a ticker.
        
        Args:
            ticker (str): Ticker symbol
        
        Returns:
            Tuple[datetime, datetime]: (start_date, end_date)
        
        Raises:
            ValueError: If ticker not found
            RuntimeError: If database error occurs
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT MIN(date), MAX(date) FROM ohlc_data WHERE ticker = ?",
                (ticker,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result[0] is None:
                raise ValueError(f"No data found for ticker: {ticker}")
            
            start_date = datetime.fromisoformat(result[0])
            end_date = datetime.fromisoformat(result[1])
            
            return (start_date, end_date)
        
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
    
    def get_ticker_info(self, ticker: str) -> Dict[str, any]:
        """
        Get information about a ticker.
        
        Args:
            ticker (str): Ticker symbol
        
        Returns:
            Dict with ticker information
        
        Raises:
            ValueError: If ticker not found
        """
        try:
            df = self.get_ohlcv_data(ticker)
            start_date, end_date = self.get_date_range(ticker)
            
            return {
                'ticker': ticker,
                'start_date': start_date,
                'end_date': end_date,
                'record_count': len(df),
                'current_price': float(df['close'].iloc[-1]),
                'highest_price': float(df['high'].max()),
                'lowest_price': float(df['low'].min()),
                'average_volume': float(df['volume'].mean())
            }
        
        except (ValueError, RuntimeError) as e:
            raise ValueError(f"Error getting info for {ticker}: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate OHLCV DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame to validate
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        
        if df.empty:
            errors.append("DataFrame is empty")
            return (False, errors)
        
        missing_cols = required_columns - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check for NaN in OHLC columns
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns and df[col].isna().any():
                errors.append(f"Column '{col}' contains NaN values")
        
        # Check that high >= low
        if 'high' in df.columns and 'low' in df.columns:
            invalid = (df['high'] < df['low']).any()
            if invalid:
                errors.append("High < Low in some rows")
        
        return (len(errors) == 0, errors)
