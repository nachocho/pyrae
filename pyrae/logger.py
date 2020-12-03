import logging
from typing import Optional

DEFAULT_FORMAT_STRING = '%(asctime)s - %(levelname)-7s - %(module)s.%(funcName)s - %(message)s'
current: Optional[logging.Logger] = None


def get_numeric_level(log_level: str):
    """ Gets a numeric log level, from a string representation, as expected by the logging module.

    :param log_level: The level of logging used:
                        DEBUG:   Detailed information, typically of interest only when diagnosing problems.
                        INFO:    Confirmation that things are working as expected.
                        WARNING: An indication that something unexpected happened, but processing continues.
                        ERROR:   A serious problem that causes processing to stop.
    :return: A numeric log level.
    """
    log_level = log_level.upper()
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    return numeric_level


def init_logger(log_level: str = 'INFO') -> logging.Logger:
    """ Initializes the global logger.

    :param log_level: The level of logging used:
                        DEBUG:   Detailed information, typically of interest only when diagnosing problems.
                        INFO:    Confirmation that things are working as expected.
                        WARNING: An indication that something unexpected happened, but processing continues.
                        ERROR:   A serious problem that causes processing to stop.
    :return: The initialized logger instance.
    """
    logger = logging.getLogger(name='pyrae')
    logger.setLevel(level=get_numeric_level(log_level))
    if len(logger.handlers) > 0:
        # Logger has already been initialized, so just set the logger with the given name.
        # This prevents duplicate handlers being added to the logger.
        return logger
    logger.propagate = False
    formatter = logging.Formatter(DEFAULT_FORMAT_STRING)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    global current
    current = logger
    return logger
