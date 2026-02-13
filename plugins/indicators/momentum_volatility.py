"""
Relative Strength Index (RSI) Indicator Plugin

Momentum indicator that measures the magnitude of recent price changes
to evaluate overbought or oversold conditions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from plugins.base_indicator import BaseIndicator, ParameterDefinition, PlotConfig


class RelativeStrengthIndex(BaseIndicator):
    """
    Relative Strength Index (RSI)
    
    Momentum oscillator that measures the speed and magnitude of price changes.
    RSI oscillates between 0 and 100. Typically:
    - RSI > 70: Overbought condition
    - RSI < 30: Oversold condition
    
    Output Columns:
        - RSI_{period}: The RSI values
    """
    
    name = "Relative Strength Index"
    version = "1.0.0"
    description = "Calculate the Relative Strength Index (RSI) momentum indicator"
    author = "Market Data Team"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """Define the period parameter for RSI."""
        return {
            "period": ParameterDefinition(
                name="period",
                type="int",
                default=14,
                min_value=2,
                max_value=100,
                step=1,
                description="Number of periods for RSI calculation"
            ),
            "overbought": ParameterDefinition(
                name="overbought",
                type="int",
                default=70,
                min_value=50,
                max_value=100,
                step=1,
                description="Overbought threshold line"
            ),
            "oversold": ParameterDefinition(
                name="oversold",
                type="int",
                default=30,
                min_value=0,
                max_value=50,
                step=1,
                description="Oversold threshold line"
            )
        }
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the Relative Strength Index.
        
        Args:
            df (pd.DataFrame): OHLCV data with 'close' column
        
        Returns:
            pd.DataFrame: Original data with RSI columns added
        """
        # Validate input data
        is_valid, errors = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        if 'close' not in df.columns:
            raise KeyError("DataFrame must contain 'close' column")
        
        period = self.parameters['period'].default
        
        if period > len(df):
            raise ValueError(
                f"Period ({period}) cannot be greater than data length ({len(df)})"
            )
        
        df_copy = df.copy()
        
        # Calculate price changes
        delta = df_copy['close'].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        df_copy[f'RSI_{period}'] = rsi
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        """Define how the RSI should be plotted."""
        period = self.parameters['period'].default
        overbought = self.parameters['overbought'].default
        oversold = self.parameters['oversold'].default
        
        return [
            PlotConfig(
                name=f"RSI({period})",
                type="line",
                yaxis="y2",
                color="purple",
                line_width=2,
                line_dash="solid",
                opacity=0.8,
                legend=True,
                showlegend=True
            ),
            PlotConfig(
                name="Overbought (70)",
                type="line",
                yaxis="y2",
                color="red",
                line_width=1,
                line_dash="dash",
                opacity=0.5,
                legend=True,
                showlegend=True
            ),
            PlotConfig(
                name="Oversold (30)",
                type="line",
                yaxis="y2",
                color="green",
                line_width=1,
                line_dash="dash",
                opacity=0.5,
                legend=True,
                showlegend=True
            )
        ]


class BollingerBands(BaseIndicator):
    """
    Bollinger Bands Indicator
    
    Volatility indicator consisting of:
    - Middle Band: SMA
    - Upper Band: SMA + (std_dev * multiplier)
    - Lower Band: SMA - (std_dev * multiplier)
    
    Useful for identifying overbought/oversold and volatility.
    
    Output Columns:
        - BB_Middle_{period}: The middle band (SMA)
        - BB_Upper_{period}: The upper band
        - BB_Lower_{period}: The lower band
        - BB_Width_{period}: The width of the bands
    """
    
    name = "Bollinger Bands"
    version = "1.0.0"
    description = "Calculate Bollinger Bands volatility indicator"
    author = "Market Data Team"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """Define the parameters for Bollinger Bands."""
        return {
            "period": ParameterDefinition(
                name="period",
                type="int",
                default=20,
                min_value=2,
                max_value=500,
                step=1,
                description="Number of periods for SMA and standard deviation"
            ),
            "multiplier": ParameterDefinition(
                name="multiplier",
                type="float",
                default=2.0,
                min_value=0.5,
                max_value=5.0,
                step=0.1,
                description="Standard deviation multiplier for bands"
            )
        }
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            df (pd.DataFrame): OHLCV data with 'close' column
        
        Returns:
            pd.DataFrame: Original data with Bollinger Bands columns added
        """
        # Validate input data
        is_valid, errors = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        if 'close' not in df.columns:
            raise KeyError("DataFrame must contain 'close' column")
        
        period = self.parameters['period'].default
        multiplier = self.parameters['multiplier'].default
        
        if period > len(df):
            raise ValueError(
                f"Period ({period}) cannot be greater than data length ({len(df)})"
            )
        
        df_copy = df.copy()
        
        # Calculate middle band (SMA)
        middle_band = df_copy['close'].rolling(window=period).mean()
        
        # Calculate standard deviation
        std_dev = df_copy['close'].rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * multiplier)
        lower_band = middle_band - (std_dev * multiplier)
        
        # Calculate bandwidth
        band_width = upper_band - lower_band
        
        # Add to dataframe
        df_copy[f'BB_Middle_{period}'] = middle_band
        df_copy[f'BB_Upper_{period}'] = upper_band
        df_copy[f'BB_Lower_{period}'] = lower_band
        df_copy[f'BB_Width_{period}'] = band_width
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        """Define how the Bollinger Bands should be plotted."""
        period = self.parameters['period'].default
        
        return [
            PlotConfig(
                name=f"BB Upper({period})",
                type="line",
                yaxis="y",
                color="gray",
                line_width=1,
                line_dash="dash",
                opacity=0.6,
                legend=True,
                showlegend=True
            ),
            PlotConfig(
                name=f"BB Middle({period})",
                type="line",
                yaxis="y",
                color="blue",
                line_width=2,
                line_dash="solid",
                opacity=0.8,
                legend=True,
                showlegend=True
            ),
            PlotConfig(
                name=f"BB Lower({period})",
                type="line",
                yaxis="y",
                color="gray",
                line_width=1,
                line_dash="dash",
                opacity=0.6,
                legend=True,
                showlegend=True
            )
        ]
