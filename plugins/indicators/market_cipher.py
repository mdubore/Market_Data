"""
Market Cipher Indicator Plugins

This module contains implementations of Market Cipher A and Market Cipher B
technical indicators for cryptocurrency and stock market analysis.

Market Cipher A: Wave Trend oscillator with momentum signals
Market Cipher B: Multi-indicator confluence with Money Flow and momentum dots
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from plugins.base_indicator import BaseIndicator, ParameterDefinition, PlotConfig


class MarketCipherA(BaseIndicator):
    """
    Market Cipher A - Wave Trend Oscillator
    
    A momentum oscillator that identifies overbought/oversold conditions
    and generates buy/sell signals through wave trend crossovers.
    
    Components:
    - WT1 (Wave Trend 1): Fast wave trend line
    - WT2 (Wave Trend 2): Slow wave trend line (SMA of WT1)
    - Crossover signals for entry/exit points
    """
    
    name = "Market Cipher A"
    version = "1.0.0"
    description = "Wave Trend oscillator with momentum crossover signals"
    author = "Market Data Team"
    category = "momentum"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """Define indicator parameters."""
        return {
            "channel_length": ParameterDefinition(
                name="channel_length",
                type="int",
                default=9,
                min_value=5,
                max_value=20,
                step=1,
                description="Channel length for EMA calculation"
            ),
            "average_length": ParameterDefinition(
                name="average_length",
                type="int",
                default=12,
                min_value=5,
                max_value=30,
                step=1,
                description="Average length for wave trend smoothing"
            ),
            "overbought": ParameterDefinition(
                name="overbought",
                type="int",
                default=60,
                min_value=50,
                max_value=80,
                step=5,
                description="Overbought threshold level"
            ),
            "oversold": ParameterDefinition(
                name="oversold",
                type="int",
                default=-60,
                min_value=-80,
                max_value=-50,
                step=5,
                description="Oversold threshold level"
            )
        }
    
    def _ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()
    
    def _hlc3(self, df: pd.DataFrame) -> pd.Series:
        """Calculate typical price (HLC3)."""
        return (df['high'] + df['low'] + df['close']) / 3
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Market Cipher A (Wave Trend).
        
        Args:
            df (pd.DataFrame): OHLCV data
        
        Returns:
            pd.DataFrame: Original data with Wave Trend columns added
        """
        # Validate input data
        is_valid, errors = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        required_cols = ['high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise KeyError(f"DataFrame must contain '{col}' column")
        
        channel_length = self.parameters['channel_length'].default
        average_length = self.parameters['average_length'].default
        
        df_copy = df.copy()
        
        # Calculate HLC3 (typical price)
        hlc3 = self._hlc3(df_copy)
        
        # Calculate EMA of HLC3
        esa = self._ema(hlc3, channel_length)
        
        # Calculate EMA of absolute difference
        d = self._ema(abs(hlc3 - esa), channel_length)
        
        # Calculate CI (Commodity Index)
        # Add small epsilon to avoid division by zero
        ci = (hlc3 - esa) / (0.015 * d + 1e-10)
        
        # Calculate Wave Trend 1 (WT1)
        wt1 = self._ema(ci, average_length)
        
        # Calculate Wave Trend 2 (WT2) - SMA of WT1
        wt2 = wt1.rolling(window=4).mean()
        
        # Calculate histogram (difference between WT1 and WT2)
        wt_hist = wt1 - wt2
        
        # Add to dataframe
        df_copy['MCA_WT1'] = wt1
        df_copy['MCA_WT2'] = wt2
        df_copy['MCA_Hist'] = wt_hist
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        """Define how Market Cipher A should be plotted."""
        return [
            PlotConfig(
                name="MCA_WT1",
                type="line",
                yaxis="y2",
                color="#00bcd4",  # Cyan
                line_width=2,
                line_dash="solid",
                opacity=0.9,
                legend=True,
                showlegend=True
            ),
            PlotConfig(
                name="MCA_WT2",
                type="line",
                yaxis="y2",
                color="#ff5722",  # Orange
                line_width=1,
                line_dash="solid",
                opacity=0.7,
                legend=True,
                showlegend=True
            )
        ]


class MarketCipherB(BaseIndicator):
    """
    Market Cipher B - Multi-Indicator Confluence
    
    A comprehensive indicator combining multiple signals:
    - Wave Trend oscillator (from Cipher A)
    - Money Flow Index
    - Momentum dots for trend confirmation
    - VWAP deviation bands
    """
    
    name = "Market Cipher B"
    version = "1.0.0"
    description = "Multi-indicator confluence with Money Flow and momentum signals"
    author = "Market Data Team"
    category = "momentum"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """Define indicator parameters."""
        return {
            "channel_length": ParameterDefinition(
                name="channel_length",
                type="int",
                default=9,
                min_value=5,
                max_value=20,
                step=1,
                description="Channel length for Wave Trend"
            ),
            "average_length": ParameterDefinition(
                name="average_length",
                type="int",
                default=12,
                min_value=5,
                max_value=30,
                step=1,
                description="Average length for Wave Trend"
            ),
            "mfi_length": ParameterDefinition(
                name="mfi_length",
                type="int",
                default=60,
                min_value=20,
                max_value=100,
                step=10,
                description="Money Flow Index length"
            ),
            "overbought": ParameterDefinition(
                name="overbought",
                type="int",
                default=53,
                min_value=40,
                max_value=70,
                step=1,
                description="Overbought threshold"
            ),
            "oversold": ParameterDefinition(
                name="oversold",
                type="int",
                default=-53,
                min_value=-70,
                max_value=-40,
                step=1,
                description="Oversold threshold"
            )
        }
    
    def _ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()
    
    def _sma(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return series.rolling(window=period).mean()
    
    def _hlc3(self, df: pd.DataFrame) -> pd.Series:
        """Calculate typical price (HLC3)."""
        return (df['high'] + df['low'] + df['close']) / 3
    
    def _calculate_mfi(self, df: pd.DataFrame, length: int) -> pd.Series:
        """
        Calculate Money Flow Index.
        
        MFI uses both price and volume to measure buying and selling pressure.
        """
        typical_price = self._hlc3(df)
        raw_money_flow = typical_price * df['volume']
        
        # Calculate positive and negative money flow
        price_change = typical_price.diff()
        
        positive_flow = pd.Series(0.0, index=df.index)
        negative_flow = pd.Series(0.0, index=df.index)
        
        positive_flow[price_change > 0] = raw_money_flow[price_change > 0]
        negative_flow[price_change < 0] = raw_money_flow[price_change < 0]
        
        # Calculate MFI
        positive_mf = positive_flow.rolling(window=length).sum()
        negative_mf = negative_flow.rolling(window=length).sum()
        
        # Add small epsilon to avoid division by zero
        mfi = 100 - (100 / (1 + positive_mf / (negative_mf + 1e-10)))
        
        # Scale MFI to oscillator range (-100 to 100)
        mfi_scaled = (mfi - 50) * 2
        
        return mfi_scaled
    
    def _calculate_wave_trend(self, df: pd.DataFrame, channel_length: int, 
                               average_length: int) -> tuple:
        """Calculate Wave Trend oscillator components."""
        hlc3 = self._hlc3(df)
        
        # EMA of HLC3
        esa = self._ema(hlc3, channel_length)
        
        # EMA of absolute difference
        d = self._ema(abs(hlc3 - esa), channel_length)
        
        # CI (Commodity Index) - add epsilon to avoid division by zero
        ci = (hlc3 - esa) / (0.015 * d + 1e-10)
        
        # Wave Trend 1 and 2
        wt1 = self._ema(ci, average_length)
        wt2 = self._sma(wt1, 4)
        
        return wt1, wt2
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Market Cipher B indicators.
        
        Args:
            df (pd.DataFrame): OHLCV data with volume
        
        Returns:
            pd.DataFrame: Original data with Market Cipher B columns added
        """
        # Validate input data
        is_valid, errors = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        required_cols = ['high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise KeyError(f"DataFrame must contain '{col}' column")
        
        channel_length = self.parameters['channel_length'].default
        average_length = self.parameters['average_length'].default
        mfi_length = self.parameters['mfi_length'].default
        overbought = self.parameters['overbought'].default
        oversold = self.parameters['oversold'].default
        
        df_copy = df.copy()
        
        # Calculate Wave Trend
        wt1, wt2 = self._calculate_wave_trend(df_copy, channel_length, average_length)
        
        # Calculate Money Flow
        mfi = self._calculate_mfi(df_copy, mfi_length)
        
        # Calculate histogram
        wt_hist = wt1 - wt2
        
        # Detect momentum dots (crossovers in oversold/overbought zones)
        # Buy dots: WT1 crosses above WT2 in oversold zone
        # Sell dots: WT1 crosses below WT2 in overbought zone
        cross_up = (wt1 > wt2) & (wt1.shift(1) <= wt2.shift(1))
        cross_down = (wt1 < wt2) & (wt1.shift(1) >= wt2.shift(1))
        
        buy_signal = cross_up & (wt2 < oversold)
        sell_signal = cross_down & (wt2 > overbought)
        
        # Add columns to dataframe
        df_copy['MCB_WT1'] = wt1
        df_copy['MCB_WT2'] = wt2
        df_copy['MCB_MFI'] = mfi
        df_copy['MCB_Hist'] = wt_hist
        df_copy['MCB_Buy'] = buy_signal.astype(int) * oversold  # Plot at oversold level
        df_copy['MCB_Sell'] = sell_signal.astype(int) * overbought  # Plot at overbought level
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        """Define how Market Cipher B should be plotted."""
        return [
            PlotConfig(
                name="MCB_WT1",
                type="line",
                yaxis="y2",
                color="#00e676",  # Green
                line_width=2,
                line_dash="solid",
                opacity=0.9,
                legend=True,
                showlegend=True
            ),
            PlotConfig(
                name="MCB_WT2",
                type="line",
                yaxis="y2",
                color="#ff1744",  # Red
                line_width=1,
                line_dash="solid",
                opacity=0.7,
                legend=True,
                showlegend=True
            ),
            PlotConfig(
                name="MCB_MFI",
                type="line",
                yaxis="y2",
                color="#ffeb3b",  # Yellow
                line_width=1,
                line_dash="dot",
                opacity=0.6,
                legend=True,
                showlegend=True
            )
        ]
