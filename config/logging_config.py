"""This file is used to configure logger configs"""

import logging


def configure_logging():
    """
    This is just a function to configure the general logger,
    it should be called when the application starts.
    Child loggers are created in the same function and added to the main logger,
    and then you can communicate with them
    e.g. logger = logging.getLogger("schedule.db") -  logger for database
    """
    # Create main logger
    logger = logging.getLogger("shedule")
    logger.setLevel(logging.DEBUG)

    # Handler for output in console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Handler for write in file
    file_handler = logging.FileHandler("logs/shedule.log")
    file_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add formatter to handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to main logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
