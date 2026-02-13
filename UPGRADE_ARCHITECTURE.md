# Interactive Candlestick Chart Application - Architecture Design

## Overview
This document outlines the architecture for upgrading the static candlestick chart application into a modern, interactive web-based charting tool with a plugin system for custom indicators.

## Technology Stack

### Frontend & UI
- **Framework**: Streamlit or Plotly Dash (Streamlit recommended for simplicity)
- **Interactive Charting**: Plotly (replaces mplfinance)
- **Styling**: Modern CSS with custom themes

### Backend
- **Data Processing**: Pandas (retained from original)
- **Database**: SQLite (retained from original)
- **Plugin System**: Python ABC (Abstract Base Classes)

### Key Dependencies
```
plotly>=5.18.0          # Interactive charts
streamlit>=1.28.0       # Web UI framework
pandas>=3.0.0           # Data manipulation
sqlite3                 # Database (built-in)
pyyaml>=6.0            # Configuration
python>=3.9             # Minimum version
```

## Application Architecture

### Directory Structure
```
Market_Data/
├── app.py                          # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── chart_engine.py             # Interactive chart generation
│   ├── data_manager.py             # Database and data operations
│   ├── plugin_manager.py           # Plugin loader and manager
│   └── utils.py                    # Utility functions
├── plugins/
│   ├── __init__.py
│   ├── base_indicator.py           # Base plugin interface
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── simple_moving_average.py
│   │   ├── exponential_moving_average.py
│   │   ├── relative_strength_index.py
│   │   ├── moving_average_convergence_divergence.py
│   │   └── bollinger_bands.py
│   └── example_plugin_template.py  # Template for custom plugins
├── config/
│   ├── app_config.yaml
│   └── plugin_config.yaml
├── tests/
│   ├── __init__.py
│   ├── test_chart_engine.py
│   ├── test_data_manager.py
│   ├── test_plugin_system.py
│   └── test_indicators.py
├── docs/
│   ├── PLUGIN_DEVELOPMENT_GUIDE.md
│   ├── API_REFERENCE.md
│   └── USER_GUIDE.md
├── candlestick_chart.py            # Legacy application (kept for reference)
├── requirements.txt
├── app_config.yaml
└── README.md
```

## Core Components

### 1. Plugin System (Base Architecture)

#### Base Indicator Class
```python
# plugins/base_indicator.py
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Tuple

class BaseIndicator(ABC):
    """
    Abstract base class for all indicators.
    All custom indicators must inherit from this class.
    """
    
    # Metadata
    name: str                    # Display name
    version: str                 # Version
    description: str             # Description
    parameters: Dict[str, Any]   # Configurable parameters
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values.
        
        Args:
            df: OHLCV DataFrame with columns [date, open, high, low, close, volume]
            
        Returns:
            DataFrame with original columns + indicator columns
        """
        pass
    
    @abstractmethod
    def get_plot_config(self) -> Dict[str, Any]:
        """
        Return plot configuration for this indicator.
        
        Returns:
            Dict with 'type', 'yaxis', 'line_style', etc.
        """
        pass
    
    def validate_parameters(self) -> bool:
        """Validate parameter values."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for parameters."""
        pass
```

### 2. Data Manager

Responsibilities:
- Query OHLCV data from SQLite database
- Handle time scale aggregation (daily → weekly → monthly)
- Data validation and cleaning
- Caching for performance

### 3. Chart Engine

Responsibilities:
- Interactive candlestick chart generation using Plotly
- Apply multiple indicators to the same chart
- Handle zoom/pan interactions
- Time scale switching with automatic data aggregation
- Custom color schemes and styling

### 4. Plugin Manager

Responsibilities:
- Discover plugins in the `plugins/indicators/` directory
- Load and instantiate plugin classes
- Validate plugin compatibility
- Cache plugin metadata
- Provide plugin lifecycle management

### 5. Streamlit Application (UI Layer)

Features:
- Sidebar for ticker/symbol selection
- Time scale selector (Daily, Weekly, Monthly)
- Indicator selection and parameter adjustment
- Interactive chart display with Plotly
- Built-in zoom/pan via Plotly
- Download chart as PNG
- Plugin management interface

## Plugin Development Workflow

### 1. Plugin Discovery
Plugins are automatically discovered from `plugins/indicators/` directory
- Must inherit from `BaseIndicator`
- Must be importable as Python modules
- Metadata extracted from class attributes

### 2. Plugin Lifecycle
```
1. Discovery → 2. Instantiation → 3. Validation → 4. Execution → 5. Rendering
```

### 3. Plugin Interface Contract
Every plugin MUST implement:
- `calculate(df: pd.DataFrame) -> pd.DataFrame`
- `get_plot_config() -> Dict[str, Any]`
- Class attributes: `name`, `version`, `description`, `parameters`

## Time Scale Aggregation Strategy

### OHLC Bar Aggregation Rules
- **Daily**: Original data (no aggregation)
- **Weekly**: 
  - Open = First open of the week
  - High = Max high of the week
  - Low = Min low of the week
  - Close = Last close of the week
  - Volume = Sum of weekly volumes
  - Date = Last date of the week (Friday)
- **Monthly**: Same rules, applied to calendar months

### Implementation
```python
def aggregate_ohlc(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Aggregate OHLC data to specified timeframe.
    
    Args:
        df: Daily OHLC DataFrame
        timeframe: 'daily', 'weekly', or 'monthly'
    
    Returns:
        Aggregated DataFrame
    """
```

## User Interface Flow

### Main Application Flow
1. User selects ticker from dropdown
2. Chooses time scale (daily/weekly/monthly)
3. Selects indicators to display
4. Adjusts indicator parameters (via sidebar)
5. Views interactive chart with:
   - Candlestick bars
   - Multiple indicator overlays
   - Zoom/pan controls
   - Legend with toggleable series
6. Option to download chart

### Interactive Features
- **Zoom**: Box select or scroll wheel
- **Pan**: Click and drag
- **Toggle Series**: Click legend items
- **Hover**: Tooltip shows OHLCV + indicator values
- **Time Scale Switch**: Auto-reloads chart with new timeframe

## Configuration System

### app_config.yaml
```yaml
database:
  path: "market_data.db"
  
ui:
  theme: "light"  # light, dark
  chart_height: 600
  chart_width: 1200
  
indicators:
  enabled: true
  auto_load: true
  
data:
  cache_enabled: true
  cache_ttl_minutes: 60
```

## Plugin Example: Simple Moving Average

```python
from plugins.base_indicator import BaseIndicator
import pandas as pd

class SimpleMovingAverage(BaseIndicator):
    name = "Simple Moving Average"
    version = "1.0.0"
    description = "Calculate SMA for specified period"
    parameters = {
        "period": {
            "type": "int",
            "default": 20,
            "min": 2,
            "max": 500,
            "description": "Number of periods for SMA"
        }
    }
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        period = self.parameters["period"]["default"]
        df[f"SMA_{period}"] = df["close"].rolling(window=period).mean()
        return df
    
    def get_plot_config(self):
        return {
            "type": "line",
            "yaxis": "y",
            "name": f"SMA({period})",
            "line": {"color": "blue", "width": 2}
        }
```

## Performance Considerations

1. **Data Caching**: Cache aggregated data to avoid recalculation
2. **Lazy Loading**: Load plugins only when selected
3. **Incremental Updates**: Only recalculate changed indicators
4. **Database Indexing**: Ensure database has indexes on ticker and date columns
5. **Streaming**: Use Streamlit's caching decorators

## Security Considerations

1. **Plugin Validation**: Verify plugin class inheritance before loading
2. **Parameter Validation**: Strict type checking for indicator parameters
3. **SQL Injection Prevention**: Use parameterized queries (already in place)
4. **File Access**: Plugins restricted to their own directory

## Testing Strategy

1. **Unit Tests**: Test each component independently
2. **Integration Tests**: Test plugin system with multiple indicators
3. **UI Tests**: Test interactive features and time scale switching
4. **Performance Tests**: Benchmark data aggregation and chart rendering
5. **Plugin Compatibility**: Test third-party plugins

## Migration from Legacy Application

The original `candlestick_chart.py` will be preserved but superseded by the new application:
- New app: `app.py` (Streamlit-based)
- Legacy app: `candlestick_chart.py` (kept for reference)
- Users transitioned to new interactive UI
- CLI removed in favor of web UI

## Future Enhancements

1. **Multi-timeframe Analysis**: Display multiple timeframes simultaneously
2. **Alert System**: Set price alerts and indicator conditions
3. **Strategy Backtesting**: Test trading strategies against historical data
4. **Portfolio Management**: Track multiple tickers with portfolio view
5. **API Integration**: Real-time data feeds (currently uses static DB)
6. **User Accounts**: Save preferences and custom layouts
7. **Export**: Export data and analysis reports
8. **Machine Learning**: Predictive indicators using ML models

## Success Criteria

- [x] Interactive charts with Plotly
- [x] Time scale switching (daily/weekly/monthly)
- [x] Zoom and pan functionality
- [x] Plugin architecture documented
- [x] Base indicator class created
- [x] Example indicators implemented
- [x] Modern UI with Streamlit
- [x] Plugin development guide provided
- [x] Unit tests for core components
