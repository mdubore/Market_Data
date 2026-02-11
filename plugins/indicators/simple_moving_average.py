"""
Simple Moving Average (SMA) Indicator Plugin

A basic technical indicator that calculates the average closing price
over a specified number of periods.
"""

import pandas as pd
from typing import Dict, List, Any, Tuple
from plugins.base_indicator import BaseIndicator, ParameterDefinition, PlotConfig


class SimpleMovingAverage(BaseIndicator):
    """
    Simple Moving Average Indicator
    
    Calculates the arithmetic mean of prices over a specified period.
    Useful for identifying trends and support/resistance levels.
    
    Output Columns:
        - SMA_{period}: The simple moving average values
    """
    
    name = "Simple Moving Average"
    version = "1.0.0"
    description = "Calculate the simple moving average of closing prices"
    author = "Market Data Team"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """Define the period parameter for SMA."""
        return {
            "period": ParameterDefinition(
                name="period",
                type="int",
                default=20,
                min_value=2,
                max_value=500,
                step=1,
                description="Number of periods to calculate average over"
            )
        }
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the Simple Moving Average.
        
        Args:
            df (pd.DataFrame): OHLCV data with 'close' column
        
        Returns:
            pd.DataFrame: Original data with SMA column added
        
        Raises:
            ValueError: If period is invalid or data is insufficient
        """
        # Validate input data
        is_valid, errors = self.validate_data(df)
        if not errors:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        if 'close' not in df.columns:
            raise KeyError("DataFrame must contain 'close' column")
        
        # Get the period
        period = self.parameters['period'].default
        
        # Validate period
        if period > len(df):
            raise ValueError(
                f"Period ({period}) cannot be greater than data length ({len(df)})"
            )
        
        # Calculate SMA
        df_copy = df.copy()
        df_copy[f'SMA_{period}'] = df_copy['close'].rolling(window=period).mean()
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        """Define how the SMA should be plotted."""
        period = self.parameters['period'].default
        
        return [
            PlotConfig(
                name=f"SMA({period})",
                type="line",
                yaxis="y",
                color="blue",
                line_width=2,
                line_dash="solid",
                opacity=0.8,
                legend=True,
                showlegend=True
            )
        ]


class ExponentialMovingAverage(BaseIndicator):
    """
    Exponential Moving Average Indicator
    
    Gives more weight to recent prices compared to older prices.
    More responsive to recent price changes than SMA.
    
    Output Columns:
        - EMA_{period}: The exponential moving average values
    """
    
    name = "Exponential Moving Average"
    version = "1.0.0"
    description = "Calculate the exponential moving average of closing prices"
    author = "Market Data Team"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """Define the period parameter for EMA."""
        return {
            "period": ParameterDefinition(
                name="period",
                type="int",
                default=12,
                min_value=2,
                max_value=500,
                step=1,
                description="Number of periods to calculate average over"
            )
        }
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the Exponential Moving Average.
        
        Args:
            df (pd.DataFrame): OHLCV data with 'close' column
        
        Returns:
            pd.DataFrame: Original data with EMA column added
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
        df_copy[f'EMA_{period}'] = df_copy['close'].ewm(span=period, adjust=False).mean()
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        """Define how the EMA should be plotted."""
        period = self.parameters['period'].default
        
        return [
            PlotConfig(
                name=f"EMA({period})",
                type="line",
                yaxis="y",
                color="red",
                line_width=2,
                line_dash="solid",
                opacity=0.8,
                legend=True,
                showlegend=True
            )
        ]
