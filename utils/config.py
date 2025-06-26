"""
@author         : J.J.G. Pleunes
@file           : config.py
@brief          : Configuration management for the Statistical Error Detection Tools
@description    : This module provides configuration management for the Statistical Error Detection Tools.
@date           : 26-06-2025
@version        : 1.0.0
@license        : MIT License

    Copyright (c) 2025 Julius Pleunes

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    © 2025 bachelorThesis. All rights reserved.
"""

# Importing necessary libraries
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any
import json
import yaml

@dataclass
class GRIMConfig:
    """
    @class           : GRIMConfig
    @description     : Configuration for the GRIM tool.
    @attributes      :
        max_words (int): Maximum number of words to process in a single request.
        overlap_words (int): Number of overlapping words between requests.
        api_model (str): OpenAI API model to use.
        temperature (float): Sampling temperature for the model.
    @methods         :
        to_dict() -> Dict[str, Any]: Converts the configuration to a dictionary.
    @example         :
        grim_config = GRIMConfig(max_words=1000, overlap_words=200, api_model="gpt-4o", temperature=0.01)
    @return          : None
    @raises          : None
    @note            : This class is used to configure the GRIM tool for statistical error detection.
    """
    max_words: int = 1000
    overlap_words: int = 200
    api_model: str = "gpt-4o"
    temperature: float = 0.01
    
    def to_dict(self) -> Dict[str, Any]:
        """ 
        @function       : to_dict
        @description    : Converts the GRIM configuration to a dictionary.
        @return         : Dictionary representation of the configuration.
        @example        :
        >>> grim_config = GRIMConfig()
        >>> grim_dict = grim_config.to_dict()
        >>> print(grim_dict)
        @raises         : None
        @note           : This method is useful for serialization or saving the configuration to a file.
        """
        return asdict(self)


@dataclass
class StatcheckConfig:
    """
    @class           : StatcheckConfig
    @description     : Configuration for the Statcheck tool.
    @attributes      :
        max_words (int): Maximum number of words to process in a single request.
        overlap_words (int): Number of overlapping words between requests.
        api_model (str): OpenAI API model to use.
        temperature (float): Sampling temperature for the model.
        significance_level (float): Significance level for statistical tests.
    @methods         :
        to_dict() -> Dict[str, Any]: Converts the configuration to a dictionary.
    @example         :
        statcheck_config = StatcheckConfig(max_words=500, overlap_words=8, api
        model="gpt-4o-mini", temperature=0.0, significance_level=0.05)
    @return          : None
    @raises          : None
    @note            : This class is used to configure the Statcheck tool for statistical error detection.
    """
    max_words: int = 500
    overlap_words: int = 8
    api_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    significance_level: float = 0.05
    
    def to_dict(self) -> Dict[str, Any]:
        """ 
        @function       : to_dict
        @description    : Converts the Statcheck configuration to a dictionary.
        @return         : Dictionary representation of the configuration.
        @example        :
        >>> statcheck_config = StatcheckConfig()
        >>> statcheck_dict = statcheck_config.to_dict()
        >>> print(statcheck_dict)
        @raises         : None
        @note           : This method is useful for serialization or saving the configuration to a file.
        """
        return asdict(self)


@dataclass
class AppConfig:
    """
    @class           : AppConfig
    @description     : Main application configuration for the Statistical Error Detection Tools.
    @attributes      :
        openai_api_key (Optional[str]): OpenAI API key for accessing the API.
        grim (GRIMConfig): Configuration for the GRIM tool.
        statcheck (StatcheckConfig): Configuration for the Statcheck tool.
        log_level (str): Logging level (e.g., "INFO", "DEBUG").
        log_file (Optional[str]): Path to the log file.
        verbose (bool): Enable verbose logging.
        default_output_format (str): Default format for output files (e.g., "csv", "json").
    @methods         :
        to_dict() -> Dict[str, Any]: Converts the configuration to a dictionary.
    @example         :
        app_config = AppConfig(
            openai_api_key="your_api_key",  # Replace with your actual OpenAI API key
            grim=GRIMConfig(max_words=1000, overlap_words=200, api_model="gpt-4o", temperature=0.01),
            statcheck=StatcheckConfig(max_words=500, overlap_words=8, api_model="gpt-4o", temperature=0.01),
            log_level="INFO",
            log_file="app.log",
            verbose=True,
            default_output_format="csv"
        )
    @return          : None
    @raises          : None
    @note            : This class is used to manage the application's configuration settings, 
                       including API keys, tool configurations, logging settings, and output formats.
    """
    # API settings
    openai_api_key: Optional[str] = None
    
    # Tool configurations
    grim: GRIMConfig = None
    statcheck: StatcheckConfig = None
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    verbose: bool = False
    
    # Output settings
    default_output_format: str = "csv"
    
    def __post_init__(self):
        """ 
        @function       : __post_init__
        @description    : Post-initialization method to set default values and load API key from environment.
        @return         : None
        @example        :
        >>> app_config = AppConfig()
        >>> app_config.__post_init__()
        @raises         : None
        @note           : This method is called automatically after the class is initialized to ensure that
                          the configuration is properly set up with default values and environment variables.
        """
        if self.grim is None:
            self.grim = GRIMConfig()
        if self.statcheck is None:
            self.statcheck = StatcheckConfig()
        
        # Load API key from environment if not set
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def to_dict(self) -> Dict[str, Any]:
        """ 
        @function       : to_dict
        @description    : Converts the application configuration to a dictionary.
        @return         : Dictionary representation of the configuration.
        @example        :
        >>> app_config = AppConfig()    
        >>> config_dict = app_config.to_dict()
        >>> print(config_dict)
        @raises         : None
        @note           : This method is useful for serialization or saving the configuration to a file.
        """
        return {
            "openai_api_key": "***" if self.openai_api_key else None,  # Don't expose API key
            "grim": self.grim.to_dict(),
            "statcheck": self.statcheck.to_dict(),
            "log_level": self.log_level,
            "log_file": self.log_file,
            "verbose": self.verbose,
            "default_output_format": self.default_output_format,
        }


class ConfigManager:
    """
    @class           : ConfigManager
    @description     : Manages application configuration for the Statistical Error Detection Tools.
    @attributes      :
        config_path (Path): Path to the configuration file.
        _config (AppConfig): Current application configuration.
    @methods         :
        config() -> AppConfig: Get current configuration.
        load_config(config_path: Optional[str] = None) -> AppConfig: Load configuration from file.
        save_config(config_path: Optional[str] = None) -> None: Save current configuration to
        update_config(**kwargs) -> None: Update configuration parameters.
    @example         :  
        config_manager = ConfigManager("config.yaml")
        config = config_manager.load_config()
        config_manager.save_config()
    @return          : None 
    @raises          : None
    @note            : This class provides methods to load, save, and update the application configuration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """ 
        @function       : __init__
        @description    : Initializes the ConfigManager with a specified configuration file path.
        @param config_path: Path to the configuration file (default: "config.yaml").
        @return         : None
        @example        : config_manager = ConfigManager("config.yaml")
        @raises         : None
        @note           : This method sets up the configuration manager with a default path for the configuration file.
        """
        self.config_path = Path(config_path) if config_path else Path("config.yaml")
        self._config = AppConfig()
    
    @property
    def config(self) -> AppConfig:
        """
        @function       : config
        @description    : Get the current application configuration.
        @return         : Current application configuration as an AppConfig object.
        @example        :
        >>> config_manager = ConfigManager()
        >>> current_config = config_manager.config
        >>> print(current_config)
        @raises         : None
        @note           : This property provides access to the current configuration without needing to call a method
        """
        return self._config
    
    def load_config(self, config_path: Optional[str] = None) -> AppConfig:
        """
        @function       : load_config
        @description    : Load configuration from a file.
        @param config_path: Path to the configuration file (default: None, uses self.config_path).
        @return         : Loaded application configuration as an AppConfig object.
        @example        :
        >>> config_manager = ConfigManager()
        >>> config = config_manager.load_config("config.yaml")
        >>> print(config)
        @raises         : Exception if the configuration file cannot be read or parsed.
        @note           : This method reads the configuration from a specified file, creating a default configuration
                          if the file does not exist. It supports both JSON and YAML formats.
        """
        if config_path:
            self.config_path = Path(config_path)
        
        if not self.config_path.exists():
            # Create default config file
            self.save_config()
            return self._config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:  # Assume YAML
                    data = yaml.safe_load(f) or {}
            
            # Update configuration
            if 'grim' in data:
                self._config.grim = GRIMConfig(**data['grim'])
            if 'statcheck' in data:
                self._config.statcheck = StatcheckConfig(**data['statcheck'])
            
            # Update other settings
            for key in ['log_level', 'log_file', 'verbose', 'default_output_format']:
                if key in data:
                    setattr(self._config, key, data[key])
                    
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            print("Using default configuration.")
        
        return self._config
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        @function       : save_config
        @description    : Save the current configuration to a file.
        @param config_path: Path to save the configuration file (default: None, uses self.config_path).
        @return         : None
        @example        :
        >>> config_manager = ConfigManager()
        >>> config_manager.save_config("config.yaml")
        @raises         : Exception if the configuration file cannot be written.
        @note           : This method saves the current configuration to a specified file in either JSON or
                          YAML format, depending on the file extension. It creates the directory if it does not exist.
        """
        if config_path:
            self.config_path = Path(config_path)
        
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    json.dump(self._config.to_dict(), f, indent=2)
                else:  # YAML
                    yaml.dump(self._config.to_dict(), f, default_flow_style=False, indent=2)
            
            print(f"Configuration saved to: {self.config_path}")
        except Exception as e:
            print(f"Error saving config to {self.config_path}: {e}")
    
    def update_config(self, **kwargs) -> None:
        """
        @function       : update_config
        @description    : Update configuration parameters.
        @param kwargs   : Keyword arguments representing configuration parameters to update.
        @return         : None
        @example        :
        >>> config_manager = ConfigManager()
        >>> config_manager.update_config(grim={'max_words': 1500}, statcheck={'overlap_words': 10})
        @raises         : None
        @note           : This method allows updating specific configuration parameters dynamically.
        """
        
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                if key in ['grim', 'statcheck'] and isinstance(value, dict):
                    # Update nested config
                    current_config = getattr(self._config, key)
                    for nested_key, nested_value in value.items():
                        if hasattr(current_config, nested_key):
                            setattr(current_config, nested_key, nested_value)
                else:
                    setattr(self._config, key, value)


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """
    @function       : get_config
    @description    : Retrieve the current application configuration.
    @return         : Current application configuration as an AppConfig object.
    @example        :
    >>> config = get_config()
    >>> print(config)
    @raises         : None
    @note           : This function provides a simple way to access the current configuration without needing to
                      instantiate the ConfigManager class.
    """
    return config_manager.config


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    @function       : load_config
    @description    : Load configuration from a file.
    @param config_path: Path to the configuration file (default: None, uses the path
                        specified in the ConfigManager instance).
    @return         : Loaded application configuration as an AppConfig object.
    @example        :
    >>> config = load_config("config.yaml")
    >>> print(config)
    @raises         : Exception if the configuration file cannot be read or parsed.
    @note           : This function loads the configuration from a specified file, creating a default configuration
                      if the file does not exist. It supports both JSON and YAML formats.
    """
    return config_manager.load_config(config_path)


def save_config(config_path: Optional[str] = None) -> None:
    """
    @function       : save_config
    @description    : Save the current configuration to a file.
    @param config_path: Path to save the configuration file (default: None, uses the path
                        specified in the ConfigManager instance).
    @return         : None
    @example        :
    >>> save_config("config.yaml")
    @raises         : Exception if the configuration file cannot be written.
    @note           : This function saves the current configuration to a specified file in either JSON or
                      YAML format, depending on the file extension. It creates the directory if it does not exist.
    """
    config_manager.save_config(config_path)
