"""
This module contains the project wide logger. It is used to log messages from any location
in the project. It is also used to log messages to the console. It uses the logging module
to log the messages.

How to use:

    from src.project_logger import Logger

    logger = Logger(__name__)

    logger.info("This is a message")

"""

import os
import logging

directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.join(directory, "..")

# Set general logging settings
logging.basicConfig(
    filename=os.path.join(project_directory, ".log"),
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Initialize the project wide logger
project_wide_logger = logging.getLogger(__name__)

# Ensure the logging is printed to the console
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# Set the format of the logging, including the location of the logger for this logger
formatter = logging.Formatter("%(asctime)s - %(location)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
project_wide_logger.addHandler(console)


class Logger:
    """Custom logger class that adds the location of the logger to the log message. Can
    be used to log messages from any location in the project."""

    def __init__(self, location: str):
        """Initialize the logger

        Args:
            location (str): The location of the logger, usually __name__
        """
        self.location = {"location": location}

    def debug(self, message: str) -> None:
        """Log a debug message"""
        project_wide_logger.debug(message, extra=self.location)

    def info(self, message: str) -> None:
        """Log an info message"""
        project_wide_logger.info(message, extra=self.location)

    def warning(self, message: str) -> None:
        """Log a warning message"""
        project_wide_logger.warning(message, extra=self.location)

    def error(self, message: str) -> None:
        """Log an error message"""
        project_wide_logger.error(message, extra=self.location)

    def critical(self, message: str) -> None:
        """Log a critical message"""
        project_wide_logger.critical(message, extra=self.location)
