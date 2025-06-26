"""
@author         : J.J.G. Pleunes
@file           : __init__.py
@brief          : Initialization module for the Statistical Error Detection Tools
@description    : This module initializes the package and exports the main components.
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

# Importing necessary components from the utils package
from .config import get_config, load_config, save_config, ConfigManager, AppConfig
from .logging_config import setup_logging, get_logger, ProgressLogger

# Exporting the main components for easy access
__all__ = [
    'get_config', 'load_config', 'save_config', 'ConfigManager', 'AppConfig',
    'setup_logging', 'get_logger', 'ProgressLogger'
]
