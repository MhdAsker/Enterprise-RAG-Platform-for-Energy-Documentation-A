import logging
import os
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

# Ensure a "logs" directory exists at the root to store output
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILEPATH = os.path.join(LOG_DIR, "energy_docs_pipeline.log")

# 1. FILE HANDLER (Detailed, persistent, and rotating)
# We use a RotatingFileHandler so your log files don't grow infinitely huge!
# It caps out at 5MB per file and keeps the 3 most recent backups automatically.
FILE_LOG_FORMAT = "[%(asctime)s] %(name)s - %(levelname)s - %(module)s.py:%(lineno)d - %(message)s"
file_formatter = logging.Formatter(FILE_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

file_handler = RotatingFileHandler(
    filename=LOG_FILEPATH, 
    maxBytes=5 * 1024 * 1024, # 5 MB size limit
    backupCount=3             # Keep 3 backups maximum
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.DEBUG) # Save EVERYTHING to the file for debugging

# 2. CONSOLE HANDLER (Beautiful, colorized experience)
# We use 'rich' (which is already installed in your environment) to print gorgeous 
# colored outputs and format big error tracebacks cleanly in your terminal.
console_handler = RichHandler(
    rich_tracebacks=True, # Magically organizes and colorizes error tracebacks!
    markup=True,
    show_time=True,
    show_path=True,
    omit_repeated_times=False
)
console_handler.setLevel(logging.INFO) # Only show INFO and worse in the terminal so we don't spam it

def get_logger(name: str = "EnergyDocsChat") -> logging.Logger:
    """
    Retrieves a beautifully formatted, rotating custom logger.
    """
    logger = logging.getLogger(name)
    
    # Check if handlers are already attached to prevent duplicate prints
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Attach our custom handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Stop logs from bubbling up to the default base python logger (prevents double printing)
        logger.propagate = False 
        
    return logger

# Default logger instance ready to use anywhere
logger = get_logger("EnergyDocs")
