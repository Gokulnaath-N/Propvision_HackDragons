import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    # Set base logger level to DEBUG so it captures everything
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)
        
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_handler = RotatingFileHandler(
            f"logs/propvision_{current_date}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger

# Example usage:
# if __name__ == "__main__":
#     logger = get_logger("example_module")
#     logger.info("This is an info message (console & file)")
#     logger.error("This is an error message (console & file)")
