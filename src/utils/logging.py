import logging
import sys

# Define log levels and their purpose for this project:
# INFO: General application flow and success events.
# WARNING: Business logic rejections, validation failures, or potential issues.
# ERROR: System failures, database errors, and unexpected exceptions.

def configure_logging():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers = [
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str):
    return logging.getLogger(name)