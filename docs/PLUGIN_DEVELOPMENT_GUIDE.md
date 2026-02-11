# Plugin Development Guide

## Overview

The Interactive Market Data Charting application uses a plugin architecture to allow developers to create custom technical indicators and analysis tools. This guide will walk you through creating your own indicator plugin.

## Plugin Architecture

### Directory Structure

```
Market_Data/
├── plugins/
│   ├── __init__.py
│   ├── base_indicator.py          # Base class for all plugins
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── simple_moving_average.py
│   │   ├── momentum_volatility.py
│   │   └── your_indicator.py      # Your custom indicator
│   └── tests/
│       └── test_plugins.py
├── src/
│   ├── plugin_manager.py          # Plugin discovery and loading
│   └── chart_engine.py            # Chart rendering
└── app.py                         # Main Streamlit app
```

## Creating a Plugin

### Step 1: Create Your Indicator Class

Create a new Python file in `plugins/indicators/` and inherit from `BaseIndicator`:

```python
from plugins.base_indicator import BaseIndicator, ParameterDefinition, PlotConfig
import pandas as pd
from typing import Dict, List

class MyCustomIndicator(BaseIndicator):
    """
    Brief description of your indicator.
    
    Longer description explaining what this indicator does,
    how it's calculated, and what it's useful for.
    
    Output Columns:
        - CUSTOM_VALUE: The main indicator value
    """
    
    # Required class attributes
    name = "My Custom Indicator"
    version = "1.0.0"
    description = "A detailed description of what this indicator does"
    author = "Your Name"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """Define configurable parameters for your indicator."""
        return {
            "period": ParameterDefinition(
                name="period",
                type="int",
                default=14,
                min_value=2,
                max_value=500,
                step=1,
                description="Number of periods to calculate over"
            ),
            "threshold": ParameterDefinition(
                name="threshold",
                type="float",
                default=50.0,
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                description="Threshold value for signals"
            )
        }
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values.
        
        Args:
            df (pd.DataFrame): DataFrame with OHLCV data
                Required columns: open, high, low, close, volume
        
        Returns:
            pd.DataFrame: Original DataFrame with new indicator columns added
        
        Raises:
            ValueError: If data validation fails
            KeyError: If required columns are missing
        """
        # Validate input data
        is_valid, errors = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        if 'close' not in df.columns:
            raise KeyError("DataFrame must contain 'close' column")
        
        # Get your parameters
        period = self.parameters['period'].default
        threshold = self.parameters['threshold'].default
        
        # Perform your calculation
        df_copy = df.copy()
        df_copy['CUSTOM_VALUE'] = df_copy['close'].rolling(window=period).mean()
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        """
        Define how to visualize your indicator outputs.
        
        Returns:
            List[PlotConfig]: Configuration for each output series
        """
        period = self.parameters['period'].default
        
        return [
            PlotConfig(
                name=f"Custom({period})",
                type="line",                    # line, scatter, bar, histogram
                yaxis="y",                      # y=left axis, y2=right axis
                color="blue",                   # Any valid color name or hex
                line_width=2,
                line_dash="solid",              # solid, dot, dash, longdash
                opacity=0.8,
                fill="none",                    # none, tozeroy, tonexty
                legend=True,
                showlegend=True
            )
        ]
```

### Step 2: Parameter Types and Options

The `ParameterDefinition` class supports several parameter types:

```python
# Integer parameter
"period": ParameterDefinition(
    name="period",
    type="int",
    default=20,
    min_value=2,
    max_value=500,
    step=1,
    description="Number of periods"
)

# Float parameter
"multiplier": ParameterDefinition(
    name="multiplier",
    type="float",
    default=2.0,
    min_value=0.5,
    max_value=5.0,
    step=0.1,
    description="Standard deviation multiplier"
)

# Boolean parameter
"show_signal": ParameterDefinition(
    name="show_signal",
    type="bool",
    default=True,
    description="Show signal line"
)

# Choice parameter
"ma_type": ParameterDefinition(
    name="ma_type",
    type="choice",
    default="sma",
    choices=["sma", "ema", "dema"],
    description="Type of moving average"
)

# String parameter
"label": ParameterDefinition(
    name="label",
    type="str",
    default="Custom",
    description="Custom label for indicator"
)
```

### Step 3: PlotConfig Options

Configure how your indicator outputs are visualized:

```python
PlotConfig(
    name="Indicator Name",                  # Display name
    type="line",                            # line, scatter, bar, histogram
    yaxis="y",                              # y (left) or y2 (right)
    color="#FF0000",                        # Color (name or hex)
    line_width=2,                           # Line thickness
    line_dash="solid",                      # solid, dot, dash, longdash
    opacity=0.8,                            # 0-1 transparency
    fill="none",                            # none, tozeroy, tonexty
    legend=True,                            # Show in legend
    showlegend=True                         # Display legend label
)
```

## Plugin Validation

All plugins must pass validation:

1. **Metadata**: Must have `name`, `version`, `description`, and `author`
2. **Methods**: Must implement `calculate()` and `get_plot_configs()`
3. **Data Handling**: Must validate input data and handle errors gracefully
4. **Parameters**: Must have consistent parameter definitions

## Testing Your Plugin

### Manual Testing

```python
from src.data_manager import DataManager
from plugins.indicators.your_indicator import YourIndicator

# Load data
data_manager = DataManager("market_data.db")
df = data_manager.get_ohlcv_data("AAPL")

# Create indicator instance
indicator = YourIndicator()

# Calculate
df_result = indicator.calculate(df)

# Get plot config
configs = indicator.get_plot_configs()
```

### Unit Testing

Create `tests/test_your_indicator.py`:

```python
import pytest
import pandas as pd
import numpy as np
from plugins.indicators.your_indicator import YourIndicator
from src.data_manager import DataManager

class TestYourIndicator:
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data."""
        dates = pd.date_range('2023-01-01', periods=100)
        return pd.DataFrame({
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
    
    def test_indicator_calculation(self, sample_data):
        """Test that indicator calculates without error."""
        indicator = YourIndicator()
        result = indicator.calculate(sample_data)
        
        assert len(result) == len(sample_data)
        assert 'CUSTOM_VALUE' in result.columns
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        indicator = YourIndicator()
        
        # Valid parameters
        is_valid, errors = indicator.validate_parameters({'period': 20})
        assert is_valid
        
        # Invalid parameters
        is_valid, errors = indicator.validate_parameters({'period': -5})
        assert not is_valid
```

## Best Practices

### 1. Data Validation

Always validate input data:

```python
def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
    is_valid, errors = self.validate_data(df)
    if not is_valid:
        raise ValueError(f"Data validation failed: {'; '.join(errors)}")
```

### 2. Error Handling

Provide clear error messages:

```python
try:
    # Your calculation
    pass
except Exception as e:
    raise RuntimeError(f"Error in MyIndicator: {e}")
```

### 3. Documentation

Document your indicator thoroughly:

```python
class MyIndicator(BaseIndicator):
    """
    Brief one-line description.
    
    Longer description explaining:
    - What the indicator does
    - How it's calculated
    - When to use it
    - Typical parameter ranges
    
    Output Columns:
        - COLUMN_NAME: Description
        - ANOTHER_COLUMN: Description
    
    Example:
        >>> indicator = MyIndicator()
        >>> result = indicator.calculate(df)
        >>> print(result.columns)
    """
```

### 4. Parameter Naming

Use descriptive parameter names:

```python
# Good
"exponential_smoothing_factor"
"upper_band_multiplier"
"signal_threshold"

# Avoid
"x"
"val"
"foo"
```

### 5. Performance

Optimize for performance with large datasets:

```python
# Good: Vectorized operations
df_copy['result'] = df_copy['close'].rolling(window=period).mean()

# Avoid: Loops
for i in range(len(df_copy)):
    df_copy.loc[i, 'result'] = df_copy.loc[i:i+period, 'close'].mean()
```

## Plugin Distribution

To share your plugin:

1. **Package it**: Create a properly structured Python package
2. **Document it**: Include README with usage examples
3. **Test it**: Ensure it passes all validation tests
4. **Share it**: Contribute to the project via GitHub PR

## Examples

### Example 1: Moving Average Convergence Divergence (MACD)

See `plugins/indicators/simple_moving_average.py` for reference implementation.

### Example 2: Custom Oscillator

```python
from plugins.base_indicator import BaseIndicator, ParameterDefinition, PlotConfig

class CustomOscillator(BaseIndicator):
    name = "Custom Oscillator"
    version = "1.0.0"
    description = "A custom oscillator indicator"
    author = "Your Name"
    
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        return {
            "fast_period": ParameterDefinition(
                name="fast_period", type="int", default=10,
                min_value=2, max_value=100, description="Fast moving average period"
            ),
            "slow_period": ParameterDefinition(
                name="slow_period", type="int", default=20,
                min_value=2, max_value=200, description="Slow moving average period"
            )
        }
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        is_valid, errors = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")
        
        fast_period = self.parameters['fast_period'].default
        slow_period = self.parameters['slow_period'].default
        
        df_copy = df.copy()
        fast_ma = df_copy['close'].ewm(span=fast_period).mean()
        slow_ma = df_copy['close'].ewm(span=slow_period).mean()
        
        df_copy['OSCILLATOR'] = fast_ma - slow_ma
        
        return df_copy
    
    def get_plot_configs(self) -> List[PlotConfig]:
        return [
            PlotConfig(
                name="Oscillator",
                type="line",
                yaxis="y2",
                color="purple",
                line_width=2
            )
        ]
```

## Troubleshooting

### Plugin Not Loading

Check the plugin manager logs:

```python
from src.plugin_manager import PluginManager

pm = PluginManager()
results = pm.load_all_plugins()

for module_name, (success, error) in results.items():
    if not success:
        print(f"Failed to load {module_name}: {error}")
```

### Data Validation Issues

Ensure your data has all required columns:

```python
required = {'open', 'high', 'low', 'close', 'volume'}
missing = required - set(df.columns)
if missing:
    print(f"Missing columns: {missing}")
```

### NaN Values

Handle NaN values properly:

```python
# Check for NaN
if df['close'].isna().any():
    # Either drop or fill NaN
    df = df.dropna()
    # or
    df = df.fillna(method='ffill')
```

## Support

For questions or issues with plugin development:

1. Check the example plugins in `plugins/indicators/`
2. Review the base class documentation in `plugins/base_indicator.py`
3. Create an issue on GitHub with your question
4. Submit a PR with your new indicator

## License

All plugins contributed to this project should follow the same license as the main project.
