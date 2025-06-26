"""
@author         : J.J.G. Pleunes
@file           : logging_config.py
@brief          : Logging configuration and utilities for the Statistical Error Detection Tools
@description    : This module provides logging configuration and utility functions for the Statistical Error Detection Tools.
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

# Import necessary libraries
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    verbose: bool = False
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        verbose: Enable verbose logging
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("stat_error_detector")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if verbose:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "stat_error_detector") -> logging.Logger:
    """
    @function           : get_logger
    @description        : Retrieve a logger instance with the specified name.
    @param name         : Name of the logger (default: 'stat_error_detector')
    @return             : Configured logger instance
    @example            :
    >>> logger = get_logger()
    >>> logger.info("This is an info message.")
    """
    return logging.getLogger(name)


class ProgressLogger:
    """
    @class              : ProgressLogger
    @description        : A simple progress logger to track the progress of tasks.
    @param total        : Total number of tasks
    @param description  : Description of the task being processed
    @example            :
    >>> progress = ProgressLogger(total=100, description="Processing")
    >>> for i in range(100):
    >>>     progress.update()
    >>> progress.finish()
    @note               : This class provides a simple way to log progress updates in the console.
    """
    
    def __init__(self, total: int, description: str = "Processing"):
        """ 
        @function           : __init__
        @description        : Initialize the ProgressLogger with total tasks and a description.
        @param total        : Total number of tasks to track progress for
        @param description  : Description of the task being processed
        @return             : None
        @example            :
        >>> progress = ProgressLogger(total=100, description="Processing")
        >>> progress.update()
        >>> progress.finish()
        @note               : This class provides a simple way to log progress updates in the console.
        """
        self.total = total
        self.current = 0
        self.description = description
        self.logger = get_logger()
    
    def update(self, increment: int = 1) -> None:
        """
        @function           : update
        @description        : Update the progress by a specified increment.
        @param increment    : Number of tasks completed in this update (default: 1)
        @return             : None
        @example            :
        >>> progress = ProgressLogger(total=100, description="Processing")
        >>> for i in range(100):
        >>>     progress.update()
        >>> progress.finish()
        @note               : This method logs the current progress and percentage completion.
        """
        self.current += increment
        if self.total > 0:
            percentage = (self.current / self.total) * 100
            self.logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)")
        else:
            self.logger.info(f"{self.description}: {self.current}")
    
    def finish(self) -> None:
        """
        @function           : finish
        @description        : Log the completion of the task.
        @return             : None
        @example            :
        >>> progress = ProgressLogger(total=100, description="Processing")
        >>> for i in range(100):
        >>>     progress.update()
        >>> progress.finish()
        @note               : This method logs a final message indicating the task is complete.
        """
        self.logger.info(f"{self.description}: Completed ({self.current}/{self.total})")
