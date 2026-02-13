"""
Unit tests for Plugin System
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import sys

from plugins.base_indicator import BaseIndicator, ParameterDefinition, PlotConfig
from src.plugin_manager import PluginManager


# Sample test indicator
class TestIndicator(BaseIndicator):
    """Sample indicator for testing."""
    
    name = "Test Indicator"
    version = "1.0.0"
    description = "A test indicator"
    author = "Test Author"
    
    def _define_parameters(self):
        return {
            "period": ParameterDefinition(
                name="period",
                type="int",
                default=20,
                min_value=2,
                max_value=500,
                step=1,
                description="Test period"
            ),
            "threshold": ParameterDefinition(
                name="threshold",
                type="float",
                default=50.0,
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                description="Test threshold"
            )
        }
    
    def calculate(self, df):
        is_valid, errors = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {errors}")
        
        df_copy = df.copy()
        period = self.parameters['period'].default
        df_copy['TEST_VALUE'] = df_copy['close'].rolling(window=period).mean()
        
        return df_copy
    
    def get_plot_configs(self):
        return [
            PlotConfig(
                name="Test(20)",
                type="line",
                yaxis="y",
                color="blue",
                line_width=2
            )
        ]


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data."""
    dates = pd.date_range('2023-01-01', periods=100)
    return pd.DataFrame({
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(110, 120, 100),
        'low': np.random.uniform(90, 100, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)


class TestParameterDefinition:
    """Test ParameterDefinition class."""
    
    def test_int_parameter_valid(self):
        """Test valid integer parameter."""
        param = ParameterDefinition(
            name="period",
            type="int",
            default=20,
            min_value=2,
            max_value=500,
            step=1
        )
        
        is_valid, error = param.validate(20)
        assert is_valid
        assert error is None
    
    def test_int_parameter_invalid_type(self):
        """Test invalid integer parameter type."""
        param = ParameterDefinition(
            name="period",
            type="int",
            default=20
        )
        
        is_valid, error = param.validate("20")
        assert not is_valid
        assert "Expected int" in error
    
    def test_int_parameter_out_of_range(self):
        """Test integer parameter out of range."""
        param = ParameterDefinition(
            name="period",
            type="int",
            default=20,
            min_value=2,
            max_value=100
        )
        
        is_valid, error = param.validate(150)
        assert not is_valid
        assert "above maximum" in error
    
    def test_float_parameter_valid(self):
        """Test valid float parameter."""
        param = ParameterDefinition(
            name="threshold",
            type="float",
            default=50.0,
            min_value=0.0,
            max_value=100.0
        )
        
        is_valid, error = param.validate(50.0)
        assert is_valid
    
    def test_bool_parameter_valid(self):
        """Test valid boolean parameter."""
        param = ParameterDefinition(
            name="show_signal",
            type="bool",
            default=True
        )
        
        is_valid, error = param.validate(True)
        assert is_valid
    
    def test_choice_parameter_valid(self):
        """Test valid choice parameter."""
        param = ParameterDefinition(
            name="ma_type",
            type="choice",
            default="sma",
            choices=["sma", "ema", "dema"]
        )
        
        is_valid, error = param.validate("ema")
        assert is_valid
    
    def test_choice_parameter_invalid(self):
        """Test invalid choice parameter."""
        param = ParameterDefinition(
            name="ma_type",
            type="choice",
            default="sma",
            choices=["sma", "ema", "dema"]
        )
        
        is_valid, error = param.validate("invalid")
        assert not is_valid


class TestPlotConfig:
    """Test PlotConfig class."""
    
    def test_valid_plot_config(self):
        """Test valid plot configuration."""
        config = PlotConfig(
            name="Test",
            type="line",
            yaxis="y",
            color="blue",
            line_width=2
        )
        
        is_valid, error = config.validate()
        assert is_valid
        assert error is None
    
    def test_invalid_plot_type(self):
        """Test invalid plot type."""
        config = PlotConfig(
            name="Test",
            type="invalid"
        )
        
        is_valid, error = config.validate()
        assert not is_valid
    
    def test_invalid_opacity(self):
        """Test invalid opacity value."""
        config = PlotConfig(
            name="Test",
            opacity=1.5
        )
        
        is_valid, error = config.validate()
        assert not is_valid


class TestBaseIndicator:
    """Test BaseIndicator abstract class."""
    
    def test_indicator_initialization(self):
        """Test indicator initialization."""
        indicator = TestIndicator()
        
        assert indicator.name == "Test Indicator"
        assert indicator.version == "1.0.0"
        assert indicator.author == "Test Author"
        assert 'period' in indicator.parameters
        assert 'threshold' in indicator.parameters
    
    def test_indicator_missing_name(self):
        """Test that indicator requires name."""
        class InvalidIndicator(BaseIndicator):
            version = "1.0.0"
            author = "Test"
            
            def _define_parameters(self):
                return {}
            
            def calculate(self, df):
                return df
            
            def get_plot_configs(self):
                return []
        
        with pytest.raises(ValueError):
            InvalidIndicator()
    
    def test_validate_data_valid(self, sample_ohlcv_data):
        """Test data validation with valid data."""
        indicator = TestIndicator()
        is_valid, errors = indicator.validate_data(sample_ohlcv_data)
        
        assert is_valid
        assert errors == []
    
    def test_validate_data_missing_columns(self):
        """Test data validation with missing columns."""
        indicator = TestIndicator()
        df = pd.DataFrame({'open': [100], 'close': [101]})
        
        is_valid, errors = indicator.validate_data(df)
        assert not is_valid
    
    def test_validate_parameters_valid(self):
        """Test parameter validation with valid params."""
        indicator = TestIndicator()
        is_valid, errors = indicator.validate_parameters({'period': 30})
        
        assert is_valid
        assert errors == []
    
    def test_validate_parameters_invalid(self):
        """Test parameter validation with invalid params."""
        indicator = TestIndicator()
        is_valid, errors = indicator.validate_parameters({'period': -5})
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_set_parameters(self):
        """Test setting parameters."""
        indicator = TestIndicator()
        is_valid, errors = indicator.set_parameters({'period': 40})
        
        assert is_valid
        assert indicator.parameters['period'].default == 40
    
    def test_get_parameters(self):
        """Test getting parameters."""
        indicator = TestIndicator()
        params = indicator.get_parameters()
        
        assert params['period'] == 20
        assert params['threshold'] == 50.0
    
    def test_indicator_calculation(self, sample_ohlcv_data):
        """Test indicator calculation."""
        indicator = TestIndicator()
        df_result = indicator.calculate(sample_ohlcv_data)
        
        assert len(df_result) == len(sample_ohlcv_data)
        assert 'TEST_VALUE' in df_result.columns
        assert df_result['TEST_VALUE'].notna().sum() > 0
    
    def test_get_plot_configs(self):
        """Test getting plot configurations."""
        indicator = TestIndicator()
        configs = indicator.get_plot_configs()
        
        assert isinstance(configs, list)
        assert len(configs) > 0
        assert all(isinstance(c, PlotConfig) for c in configs)
    
    def test_get_metadata(self):
        """Test getting indicator metadata."""
        indicator = TestIndicator()
        metadata = indicator.get_metadata()
        
        assert metadata['name'] == "Test Indicator"
        assert metadata['version'] == "1.0.0"
        assert metadata['author'] == "Test Author"
        assert 'parameters' in metadata
        assert 'outputs' in metadata


class TestPluginManager:
    """Test PluginManager class."""
    
    def test_plugin_manager_initialization(self):
        """Test PluginManager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            indicators_dir = Path(tmpdir) / "indicators"
            indicators_dir.mkdir()
            
            pm = PluginManager(str(indicators_dir))
            assert pm.plugins_dir == indicators_dir
            assert pm.loaded_plugins == {}
    
    def test_plugin_manager_missing_directory(self):
        """Test PluginManager with missing directory."""
        with pytest.raises(FileNotFoundError):
            PluginManager("/nonexistent/path")
    
    def test_discover_plugins(self):
        """Test plugin discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            indicators_dir = Path(tmpdir) / "indicators"
            indicators_dir.mkdir()
            
            # Create dummy plugin files
            (indicators_dir / "test_plugin1.py").touch()
            (indicators_dir / "test_plugin2.py").touch()
            (indicators_dir / "__init__.py").touch()
            
            pm = PluginManager(str(indicators_dir))
            plugins = pm.discover_plugins()
            
            assert 'test_plugin1' in plugins
            assert 'test_plugin2' in plugins
            assert '__init__' not in plugins
    
    def test_get_available_plugins(self):
        """Test getting available plugins."""
        pm = PluginManager.__new__(PluginManager)
        pm.loaded_plugins = {
            'Test Indicator': TestIndicator,
            'Another Indicator': TestIndicator
        }
        pm.plugin_instances = {}
        pm.plugin_metadata = {}
        
        plugins = pm.get_available_plugins()
        assert 'Test Indicator' in plugins
        assert 'Another Indicator' in plugins
    
    def test_get_plugin(self):
        """Test getting a plugin instance."""
        pm = PluginManager.__new__(PluginManager)
        pm.loaded_plugins = {'Test Indicator': TestIndicator}
        pm.plugin_instances = {}
        pm.plugin_metadata = {}
        
        plugin = pm.get_plugin('Test Indicator')
        assert isinstance(plugin, TestIndicator)
    
    def test_get_plugin_not_found(self):
        """Test getting non-existent plugin."""
        pm = PluginManager.__new__(PluginManager)
        pm.loaded_plugins = {}
        pm.plugin_instances = {}
        pm.plugin_metadata = {}
        
        plugin = pm.get_plugin('Nonexistent')
        assert plugin is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
