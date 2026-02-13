"""
Interactive Chart Engine Module

Generates interactive candlestick charts with Plotly, supporting multiple
technical indicators, themes, time frame aggregation, and customization.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.data_manager import DataManager
from src.plugin_manager import PluginManager


class InteractiveChartEngine:
    """
    Generates interactive candlestick charts with advanced features.
    
    Features:
    - Interactive candlestick charts with Plotly
    - Multiple time frame support (daily, weekly, monthly)
    - Technical indicator overlay
    - Dark/light theme switching
    - Zoom and pan controls
    - Range slider and range selector
    - Volume analysis
    - Customizable styling
    
    Attributes:
        data_manager (DataManager): Data source manager
        plugin_manager (PluginManager): Technical indicator plugins
        theme (str): Current theme ('light' or 'dark')
        height (int): Chart height in pixels
        width (int): Chart width in pixels
    
    Example:
        >>> engine = InteractiveChartEngine(data_manager, plugin_manager)
        >>> fig = engine.create_candlestick_chart(
        ...     ticker="AAPL",
        ...     timeframe="daily",
        ...     indicators=["Simple Moving Average"]
        ... )
        >>> fig.show()
    """
    
    # Theme configurations
    THEMES = {
        'light': {
            'bg_color': '#ffffff',
            'paper_color': '#ffffff',
            'font_color': '#000000',
            'axis_color': '#000000',
            'grid_color': '#26a69a',
            'candle_bullish': '#26a69a',
            'candle_bearish': '#ef5350',
            'volume_bullish': '#00aa44',
            'volume_bearish': '#ff3333'
        },
        'dark': {
            'bg_color': '#1e1e1e',
            'paper_color': '#1e1e1e',
            'font_color': '#e0e0e0',
            'axis_color': '#e0e0e0',
            'grid_color': '#404040',
            'candle_bullish': '#26d07c',
            'candle_bearish': '#f6465d',
            'volume_bullish': 'rgba(38, 208, 124, 0.5)',
            'volume_bearish': 'rgba(246, 70, 93, 0.5)'
        }
    }
    
    def __init__(
        self,
        data_manager: DataManager,
        plugin_manager: Optional[PluginManager] = None,
        theme: str = 'light',
        height: int = 600,
        width: int = 1200
    ):
        """
        Initialize the InteractiveChartEngine.
        
        Args:
            data_manager (DataManager): Data source manager
            plugin_manager (Optional[PluginManager]): Technical indicator plugins
            theme (str): Chart theme ('light' or 'dark'). Default: 'light'
            height (int): Chart height in pixels. Default: 600
            width (int): Chart width in pixels. Default: 1200
        
        Raises:
            ValueError: If theme is invalid
        """
        if theme not in self.THEMES:
            raise ValueError(f"Invalid theme: {theme}. Must be 'light' or 'dark'")
        
        self.data_manager = data_manager
        self.plugin_manager = plugin_manager
        self.theme = theme
        self.height = height
        self.width = width
    
    def change_theme(self, theme: str) -> None:
        """
        Change the chart theme.
        
        Args:
            theme (str): New theme ('light' or 'dark')
        
        Raises:
            ValueError: If theme is invalid
        """
        if theme not in self.THEMES:
            raise ValueError(f"Invalid theme: {theme}. Must be 'light' or 'dark'")
        
        self.theme = theme
    
    def get_theme_config(self) -> Dict[str, str]:
        """
        Get the current theme configuration.
        
        Returns:
            Dict[str, str]: Theme configuration dictionary
        """
        return self.THEMES[self.theme].copy()
    
    def create_candlestick_chart(
        self,
        ticker: str,
        timeframe: str = 'daily',
        indicators: Optional[List[str]] = None,
        indicator_params: Optional[Dict[str, Dict]] = None,
        title: Optional[str] = None,
        show_volume: bool = True
    ) -> go.Figure:
        """
        Create an interactive candlestick chart.
        
        Args:
            ticker (str): Stock ticker symbol
            timeframe (str): Time frame ('daily', 'weekly', 'monthly'). Default: 'daily'
            indicators (Optional[List[str]]): List of indicator names to overlay
            indicator_params (Optional[Dict[str, Dict]]): Parameters for indicators
            title (Optional[str]): Chart title. Default: auto-generated
            show_volume (bool): Show volume bars. Default: True
        
        Returns:
            go.Figure: Interactive Plotly figure
        
        Raises:
            ValueError: If ticker or timeframe is invalid
            KeyError: If indicator not found
        """
        # Validate inputs
        if timeframe not in ['daily', 'weekly', 'monthly']:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        # Get data
        df = self.data_manager.get_ohlcv_data(ticker)
        df = self.data_manager.aggregate_ohlcv(df, timeframe)
        
        # Determine number of rows for subplots
        n_subplots = 1
        if show_volume:
            n_subplots += 1
        
        # Create subplots
        fig = make_subplots(
            rows=n_subplots,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3] if show_volume else [1.0],
            subplot_titles=[]
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC',
                increasing_line_color=self.THEMES[self.theme]['candle_bullish'],
                decreasing_line_color=self.THEMES[self.theme]['candle_bearish'],
                hovertemplate=(
                    '<b>%{x|%Y-%m-%d}</b><br>'
                    'Open: $%{open:.2f}<br>'
                    'High: $%{high:.2f}<br>'
                    'Low: $%{low:.2f}<br>'
                    'Close: $%{close:.2f}<extra></extra>'
                )
            ),
            row=1,
            col=1
        )
        
        # Add volume bars
        if show_volume:
            colors = [
                self.THEMES[self.theme]['volume_bullish'] 
                if close >= open_ 
                else self.THEMES[self.theme]['volume_bearish']
                for close, open_ in zip(df['close'], df['open'])
            ]
            
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='Volume',
                    marker_color=colors,
                    showlegend=False,
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Volume: %{y:,.0f}<extra></extra>'
                ),
                row=2,
                col=1
            )
        
        # Add technical indicators
        if indicators and self.plugin_manager:
            df_with_indicators = self._add_indicators(
                df, indicators, indicator_params or {}
            )
            
            # Add indicator traces
            self._add_indicator_traces(fig, df_with_indicators, indicators, row=1)
        
        # Update layout
        self._update_layout(fig, ticker, timeframe, title)
        
        # Update x-axis with styled range selector buttons
        theme = self.THEMES[self.theme]
        fig.update_xaxes(
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1w", step="day"),
                    dict(count=1, label="1m", step="month"),
                    dict(count=3, label="3m", step="month"),
                    dict(count=6, label="6m", step="month"),
                    dict(step="all", label="All")
                ]),
                bgcolor='rgba(200, 200, 200, 0.3)' if self.theme == 'light' else 'rgba(100, 100, 100, 0.3)',
                activecolor='rgba(100, 150, 200, 0.5)' if self.theme == 'light' else 'rgba(100, 150, 200, 0.7)',
                font=dict(
                    color=theme['font_color'],
                    size=12
                )
            ),
            row=1,
            col=1
        )
        
        # Update y-axes
        fig.update_yaxes(
            title_text="Price ($)",
            title_font=dict(color=theme['axis_color'], size=12),
            tickfont=dict(color=theme['axis_color'], size=10),
            showgrid=True,
            gridwidth=1,
            gridcolor=theme['grid_color'],
            row=1,
            col=1
        )
        
        if show_volume:
            fig.update_yaxes(
                title_text="Volume",
                title_font=dict(color=theme['axis_color'], size=12),
                tickfont=dict(color=theme['axis_color'], size=10),
                showgrid=True,
                gridwidth=1,
                gridcolor=theme['grid_color'],
                row=2,
                col=1
            )
        
        # Update x-axis for volume row with matching colors
        if show_volume:
            fig.update_xaxes(
                title_font=dict(color=theme['axis_color'], size=12),
                tickfont=dict(color=theme['axis_color'], size=10),
                showgrid=True,
                gridwidth=1,
                gridcolor=theme['grid_color'],
                row=2,
                col=1
            )
        
        return fig
    
    def _add_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str],
        params: Dict[str, Dict]
    ) -> pd.DataFrame:
        """
        Add technical indicators to the dataframe.
        
        Args:
            df (pd.DataFrame): OHLCV dataframe
            indicators (List[str]): List of indicator names
            params (Dict[str, Dict]): Indicator parameters
        
        Returns:
            pd.DataFrame: DataFrame with indicator columns added
        
        Raises:
            ValueError: If indicator calculation fails
            KeyError: If indicator not found
        """
        df_with_indicators = df.copy()
        
        for indicator_name in indicators:
            if not self.plugin_manager:
                continue
            
            indicator = self.plugin_manager.get_plugin(indicator_name)
            
            if indicator is None:
                raise KeyError(f"Indicator not found: {indicator_name}")
            
            # Set parameters if provided
            if indicator_name in params:
                is_valid, errors = indicator.set_parameters(params[indicator_name])
                if not is_valid:
                    raise ValueError(
                        f"Invalid parameters for {indicator_name}: {errors}"
                    )
            
            # Calculate indicator
            try:
                df_with_indicators = indicator.calculate(df_with_indicators)
            except Exception as e:
                raise ValueError(f"Error calculating {indicator_name}: {e}")
        
        return df_with_indicators
    
    def _add_indicator_traces(
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        indicators: List[str],
        row: int = 1
    ) -> None:
        """
        Add indicator traces to the figure.
        
        Args:
            fig (go.Figure): Plotly figure
            df (pd.DataFrame): DataFrame with calculated indicators
            indicators (List[str]): List of indicator names
            row (int): Row number for trace placement
        """
        for indicator_name in indicators:
            if not self.plugin_manager:
                continue
            
            indicator = self.plugin_manager.get_plugin(indicator_name)
            
            if indicator is None:
                continue
            
            # Get plot configurations
            plot_configs = indicator.get_plot_configs()
            
            for config in plot_configs:
                # Find the column in dataframe
                column_name = None
                for col in df.columns:
                    if col.startswith(config.name.split('(')[0]):
                        column_name = col
                        break
                
                if column_name is None or df[column_name].isna().all():
                    continue
                
                # Determine y-axis
                yaxis = 'y' if config.yaxis == 'y' else 'y2'
                
                # Add trace based on type
                if config.type == 'line':
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df[column_name],
                            name=config.name,
                            mode='lines',
                            line=dict(
                                color=config.color,
                                width=config.line_width,
                                dash=config.line_dash
                            ),
                            opacity=config.opacity,
                            yaxis=yaxis,
                            hovertemplate=(
                                f'<b>{config.name}</b><br>'
                                '%{x|%Y-%m-%d}<br>'
                                'Value: %{y:.2f}<extra></extra>'
                            )
                        ),
                        row=row,
                        col=1
                    )
                
                elif config.type == 'bar':
                    fig.add_trace(
                        go.Bar(
                            x=df.index,
                            y=df[column_name],
                            name=config.name,
                            marker_color=config.color,
                            opacity=config.opacity,
                            yaxis=yaxis,
                            showlegend=config.showlegend,
                            hovertemplate=(
                                f'<b>{config.name}</b><br>'
                                '%{x|%Y-%m-%d}<br>'
                                'Value: %{y:.2f}<extra></extra>'
                            )
                        ),
                        row=row,
                        col=1
                    )
        
        # Add secondary y-axis if needed
        if any(self.plugin_manager.get_plugin(ind).get_plot_configs()[0].yaxis == 'y2' 
               for ind in indicators if self.plugin_manager.get_plugin(ind)):
            fig.update_layout(yaxis2=dict(overlaying="y", side="right"))
    
    def _update_layout(
        self,
        fig: go.Figure,
        ticker: str,
        timeframe: str,
        title: Optional[str]
    ) -> None:
        """
        Update the figure layout with theme and styling.
        
        Args:
            fig (go.Figure): Plotly figure
            ticker (str): Stock ticker
            timeframe (str): Time frame name
            title (Optional[str]): Custom title
        """
        theme = self.THEMES[self.theme]
        
        if title is None:
            title = f"{ticker} - {timeframe.capitalize()} Candlestick Chart"
        
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center',
                font=dict(size=20, color=theme['font_color'])
            ),
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template="plotly",
            hovermode='x unified',
            height=self.height,
            width=self.width,
            plot_bgcolor=theme['bg_color'],
            paper_bgcolor=theme['paper_color'],
            font=dict(color=theme['font_color'], family="Arial, sans-serif"),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=theme['grid_color'],
                title_font=dict(color=theme['axis_color'], size=12),
                tickfont=dict(color=theme['axis_color'], size=10)
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=theme['grid_color'],
                title_font=dict(color=theme['axis_color'], size=12),
                tickfont=dict(color=theme['axis_color'], size=10)
            ),
            margin=dict(l=60, r=60, t=80, b=60),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)' if self.theme == 'light' else 'rgba(30, 30, 30, 0.9)',
                bordercolor=theme['grid_color'],
                borderwidth=1,
                font=dict(color=theme['font_color'])
            )
        )
    
    def get_available_indicators(self) -> List[str]:
        """
        Get list of available indicators.
        
        Returns:
            List[str]: List of indicator names
        """
        if self.plugin_manager is None:
            return []
        
        return self.plugin_manager.get_available_plugins()
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"InteractiveChartEngine(theme={self.theme}, "
            f"size={self.width}x{self.height})"
        )
