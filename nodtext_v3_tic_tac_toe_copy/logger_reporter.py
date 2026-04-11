import logging
import os
from datetime import datetime

def setup_logging(logger_name, log_file_prefix="application"):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_name = f"{log_file_prefix}_{logger_name}.log"
    log_file_path = os.path.join(log_dir, log_file_name)

    # Create a logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False # Prevent logs from propagating to the root logger

    # Clear existing handlers to prevent duplicate logs if called multiple times
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Create a file handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler (for real-time output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging for {logger_name} started. Log file: {log_file_path}")
    return logger