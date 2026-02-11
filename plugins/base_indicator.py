"""
Base Indicator Plugin Class

Defines the abstract base class and data structures that all technical
indicator plugins must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd


@dataclass
class ParameterDefinition:
    """Defines a configurable parameter for an indicator."""
    
    name: str
    type: str  # int, float, bool, str, choice
    default: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    choices: Optional[List[str]] = None
    description: str = ""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a value against this parameter definition.
        
        Args:
            value: Value to validate
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Type validation
        if self.type == "int":
            if not isinstance(value, int):
                return (False, f"Expected int, got {type(value).__name__}")
            if self.min_value is not None and value < self.min_value:
                return (False, f"Value {value} is below minimum {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                return (False, f"Value {value} is above maximum {self.max_value}")
        
        elif self.type == "float":
            if not isinstance(value, (int, float)):
                return (False, f"Expected float, got {type(value).__name__}")
            value = float(value)
            if self.min_value is not None and value < self.min_value:
                return (False, f"Value {value} is below minimum {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                return (False, f"Value {value} is above maximum {self.max_value}")
        
        elif self.type == "bool":
            if not isinstance(value, bool):
                return (False, f"Expected bool, got {type(value).__name__}")
        
        elif self.type == "str":
            if not isinstance(value, str):
                return (False, f"Expected str, got {type(value).__name__}")
        
        elif self.type == "choice":
            if self.choices and value not in self.choices:
                return (False, f"Value '{value}' not in choices: {self.choices}")
        
        return (True, None)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class PlotConfig:
    """Defines how an indicator output should be plotted."""
    
    name: str
    type: str = "line"  # line, scatter, bar, histogram, area
    yaxis: str = "y"    # y (left) or y2 (right)
    color: str = "#000000"
    line_width: int = 2
    line_dash: str = "solid"  # solid, dot, dash, longdash
    opacity: float = 0.8
    fill: str = "none"  # none, tozeroy, tonexty
    legend: bool = True
    showlegend: bool = True
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate plot configuration."""
        valid_types = {"line", "scatter", "bar", "histogram", "area"}
        if self.type not in valid_types:
            return (False, f"Invalid plot type: {self.type}")
        
        valid_axes = {"y", "y2"}
        if self.yaxis not in valid_axes:
            return (False, f"Invalid yaxis: {self.yaxis}")
        
        valid_dashes = {"solid", "dot", "dash", "longdash"}
        if self.line_dash not in valid_dashes:
            return (False, f"Invalid line_dash: {self.line_dash}")
        
        if not (0 <= self.opacity <= 1):
            return (False, f"Opacity must be between 0 and 1, got {self.opacity}")
        
        return (True, None)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


class BaseIndicator(ABC):
    """
    Abstract base class for all technical indicator plugins.
    
    All custom indicators must inherit from this class and implement
    the abstract methods.
    
    Class Attributes (must be defined in subclasses):
        name (str): Display name of the indicator
        version (str): Version string (e.g., "1.0.0")
        description (str): Detailed description of the indicator
        author (str): Author or team name
    
    Example:
        class MyIndicator(BaseIndicator):
            name = "My Custom Indicator"
            version = "1.0.0"
            description = "Does something useful"
            author = "Your Name"
            
            def _define_parameters(self):
                return {...}
            
            def calculate(self, df):
                return df
            
            def get_plot_configs(self):
                return [...]
    """
    
    # These must be overridden in subclasses
    name: str = "Base Indicator"
    version: str = "0.0.0"
    description: str = ""
    author: str = "Unknown"
    
    def __init__(self):
        """Initialize the indicator and its parameters."""
        self.parameters: Dict[str, ParameterDefinition] = self._define_parameters()
        self._validate_class_attributes()
    
    def _validate_class_attributes(self) -> None:
        """Validate that required class attributes are defined."""
        if not self.name or self.name == "Base Indicator":
            raise ValueError(f"{self.__class__.__name__} must define 'name'")
        if not self.version:
            raise ValueError(f"{self.__class__.__name__} must define 'version'")
        if not self.author:
            raise ValueError(f"{self.__class__.__name__} must define 'author'")
    
    @abstractmethod
    def _define_parameters(self) -> Dict[str, ParameterDefinition]:
        """
        Define the parameters for this indicator.
        
        Returns:
            Dict[str, ParameterDefinition]: Dictionary of parameter definitions
        """
        return {}
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_plot_configs(self) -> List[PlotConfig]:
        """
        Get plot configuration for this indicator's outputs.
        
        Returns:
            List[PlotConfig]: List of plot configurations for each output
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate OHLCV DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame to validate
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        if df.empty:
            errors.append("DataFrame is empty")
            return (False, errors)
        
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        missing_cols = required_columns - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check for NaN in OHLC columns
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns and df[col].isna().sum() > 0:
                nan_count = df[col].isna().sum()
                errors.append(f"Column '{col}' contains {nan_count} NaN values")
        
        # Check that high >= low
        if 'high' in df.columns and 'low' in df.columns:
            invalid_rows = (df['high'] < df['low']).sum()
            if invalid_rows > 0:
                errors.append(f"{invalid_rows} rows have high < low")
        
        # Check data types
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' is not numeric")
        
        return (len(errors) == 0, errors)
    
    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate parameters against their definitions.
        
        Args:
            params (Dict[str, Any]): Parameters to validate
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Check for unknown parameters
        for param_name in params:
            if param_name not in self.parameters:
                errors.append(f"Unknown parameter: {param_name}")
        
        # Validate each parameter
        for param_name, param_def in self.parameters.items():
            if param_name in params:
                is_valid, error = param_def.validate(params[param_name])
                if not is_valid:
                    errors.append(f"Parameter '{param_name}': {error}")
        
        return (len(errors) == 0, errors)
    
    def set_parameters(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Set and validate parameters.
        
        Args:
            params (Dict[str, Any]): Parameters to set
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        is_valid, errors = self.validate_parameters(params)
        
        if is_valid:
            for param_name, value in params.items():
                self.parameters[param_name].default = value
        
        return (is_valid, errors)
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current parameter values.
        
        Returns:
            Dict[str, Any]: Current parameter values
        """
        return {
            name: param.default
            for name, param in self.parameters.items()
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get indicator metadata.
        
        Returns:
            Dict with indicator information
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'parameters': {
                name: param.to_dict()
                for name, param in self.parameters.items()
            },
            'outputs': [
                config.to_dict()
                for config in self.get_plot_configs()
            ]
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}', v{self.version})"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.name} (v{self.version}) by {self.author}"
