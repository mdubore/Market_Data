"""
Plugin Manager Module

Handles discovery, loading, validation, and management of technical indicator
plugins from the plugins/indicators directory.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC

from plugins.base_indicator import BaseIndicator


class PluginManager:
    """
    Manages the discovery, loading, and execution of indicator plugins.
    
    The PluginManager automatically discovers Python modules in the plugins/indicators
    directory, loads classes that inherit from BaseIndicator, and manages their
    lifecycle.
    
    Attributes:
        plugins_dir (Path): Directory containing indicator plugins
        loaded_plugins (Dict): Dictionary of loaded plugin classes
        plugin_instances (Dict): Dictionary of plugin instances
        plugin_metadata (Dict): Dictionary of plugin metadata
    
    Example:
        >>> pm = PluginManager("plugins/indicators")
        >>> results = pm.load_all_plugins()
        >>> available = pm.get_available_plugins()
        >>> plugin = pm.get_plugin("Simple Moving Average")
    """
    
    def __init__(self, plugins_dir: str):
        """
        Initialize the PluginManager.
        
        Args:
            plugins_dir (str): Path to the plugins/indicators directory
        
        Raises:
            FileNotFoundError: If plugins directory does not exist
        """
        self.plugins_dir = Path(plugins_dir)
        
        if not self.plugins_dir.exists():
            raise FileNotFoundError(f"Plugins directory not found: {plugins_dir}")
        
        self.loaded_plugins: Dict[str, type] = {}
        self.plugin_instances: Dict[str, BaseIndicator] = {}
        self.plugin_metadata: Dict[str, Dict] = {}
        self._plugin_module_map: Dict[str, str] = {}  # Maps plugin name to module name
    
    def discover_plugins(self) -> Dict[str, Path]:
        """
        Discover all Python files in the plugins directory.
        
        Returns:
            Dict[str, Path]: Dictionary of module names to file paths
        """
        plugins = {}
        
        try:
            for py_file in self.plugins_dir.glob("*.py"):
                # Skip __init__.py and private modules
                if py_file.name.startswith("_"):
                    continue
                
                module_name = py_file.stem
                plugins[module_name] = py_file
        
        except Exception as e:
            print(f"Error discovering plugins: {e}")
        
        return plugins
    
    def load_plugin(self, module_name: str) -> Tuple[bool, Optional[str]]:
        """
        Load a single plugin module.
        
        Args:
            module_name (str): Name of the module to load (without .py extension)
        
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            module_path = self.plugins_dir / f"{module_name}.py"
            
            if not module_path.exists():
                return (False, f"Module file not found: {module_path}")
            
            # Create module spec and load the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            
            if spec is None or spec.loader is None:
                return (False, f"Failed to create spec for {module_name}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find all BaseIndicator subclasses in the module
            loaded_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a class and a BaseIndicator subclass (but not BaseIndicator itself)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseIndicator) and 
                    attr is not BaseIndicator and
                    attr.__module__ == module.__name__):
                    
                    try:
                        # Validate the plugin
                        is_valid, error = self._validate_plugin(attr)
                        
                        if not is_valid:
                            print(f"Warning: Plugin {attr_name} validation failed: {error}")
                            continue
                        
                        # Store the plugin
                        plugin_name = attr.name
                        self.loaded_plugins[plugin_name] = attr
                        self._plugin_module_map[plugin_name] = module_name
                        
                        # Create instance and extract metadata
                        instance = attr()
                        self.plugin_instances[plugin_name] = instance
                        self.plugin_metadata[plugin_name] = instance.get_metadata()
                        
                        loaded_classes.append(plugin_name)
                    
                    except Exception as e:
                        return (False, f"Failed to instantiate {attr_name}: {e}")
            
            if not loaded_classes:
                return (False, f"No valid BaseIndicator subclasses found in {module_name}")
            
            return (True, None)
        
        except Exception as e:
            return (False, f"Error loading plugin {module_name}: {e}")
    
    def load_all_plugins(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Load all plugins from the plugins directory.
        
        Returns:
            Dict[str, Tuple[bool, Optional[str]]]: Results for each module
                Format: {module_name: (success, error_message)}
        """
        results = {}
        plugins = self.discover_plugins()
        
        for module_name in plugins:
            success, error = self.load_plugin(module_name)
            results[module_name] = (success, error)
            
            if success:
                print(f"✓ Loaded plugin: {module_name}")
            else:
                print(f"✗ Failed to load plugin {module_name}: {error}")
        
        return results
    
    def reload_plugins(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Reload all plugins.
        
        Clears existing plugins and reloads from disk. Useful for development.
        
        Returns:
            Dict[str, Tuple[bool, Optional[str]]]: Results for each module
        """
        # Clear existing plugins
        self.loaded_plugins.clear()
        self.plugin_instances.clear()
        self.plugin_metadata.clear()
        self._plugin_module_map.clear()
        
        # Reload all plugins
        return self.load_all_plugins()
    
    def _validate_plugin(self, plugin_class: type) -> Tuple[bool, Optional[str]]:
        """
        Validate a plugin class.
        
        Args:
            plugin_class (type): The plugin class to validate
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check required class attributes
        required_attrs = ['name', 'version', 'description', 'author']
        
        for attr in required_attrs:
            if not hasattr(plugin_class, attr) or not getattr(plugin_class, attr):
                return (False, f"Missing or empty '{attr}' attribute")
        
        # Check required methods
        required_methods = ['_define_parameters', 'calculate', 'get_plot_configs']
        
        for method in required_methods:
            if not hasattr(plugin_class, method):
                return (False, f"Missing required method '{method}'")
        
        # Try to instantiate and validate
        try:
            instance = plugin_class()
            
            # Check that parameters are valid
            if not isinstance(instance.parameters, dict):
                return (False, "Parameters must be a dictionary")
            
            # Check that plot configs are valid
            configs = instance.get_plot_configs()
            if not isinstance(configs, list):
                return (False, "get_plot_configs() must return a list")
        
        except Exception as e:
            return (False, f"Instantiation failed: {e}")
        
        return (True, None)
    
    def get_available_plugins(self) -> List[str]:
        """
        Get list of available plugin names.
        
        Returns:
            List[str]: List of loaded plugin names
        """
        return sorted(list(self.loaded_plugins.keys()))
    
    def get_plugin(self, plugin_name: str) -> Optional[BaseIndicator]:
        """
        Get a plugin instance by name.
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            Optional[BaseIndicator]: Plugin instance or None if not found
        """
        if plugin_name not in self.plugin_instances:
            return None
        
        return self.plugin_instances[plugin_name]
    
    def get_plugin_class(self, plugin_name: str) -> Optional[type]:
        """
        Get a plugin class by name.
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            Optional[type]: Plugin class or None if not found
        """
        return self.loaded_plugins.get(plugin_name)
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict]:
        """
        Get metadata for a plugin.
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            Optional[Dict]: Plugin metadata or None if not found
        """
        return self.plugin_metadata.get(plugin_name)
    
    def get_all_plugins_metadata(self) -> Dict[str, Dict]:
        """
        Get metadata for all loaded plugins.
        
        Returns:
            Dict[str, Dict]: Dictionary of plugin metadata
        """
        return self.plugin_metadata.copy()
    
    def get_plugin_count(self) -> int:
        """
        Get the number of loaded plugins.
        
        Returns:
            int: Number of loaded plugins
        """
        return len(self.loaded_plugins)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """
        Check if a plugin is loaded.
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            bool: True if plugin is loaded, False otherwise
        """
        return plugin_name in self.loaded_plugins
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive information about a plugin.
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            Optional[Dict]: Plugin information including metadata, module name, etc.
        """
        if plugin_name not in self.loaded_plugins:
            return None
        
        return {
            'name': plugin_name,
            'module': self._plugin_module_map.get(plugin_name),
            'class': self.loaded_plugins[plugin_name].__name__,
            'metadata': self.plugin_metadata.get(plugin_name),
            'instance': self.plugin_instances.get(plugin_name)
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"PluginManager(plugins_dir={self.plugins_dir}, "
            f"loaded={len(self.loaded_plugins)})"
        )
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return (
            f"PluginManager with {len(self.loaded_plugins)} plugins loaded:\n" +
            "\n".join(f"  - {name}" for name in self.get_available_plugins())
        )
