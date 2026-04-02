import logging
import os

# Define paths
current_dir = os.getcwd()
LogDirPath = os.path.join(current_dir, "Data")
LogFilePath = os.path.join(LogDirPath, "jarvis.log")
os.makedirs(LogDirPath, exist_ok=True)

# Configure logging
# Note: Use a rich-compatible format or standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LogFilePath, encoding='utf-8'),
        # We'll skip the StreamHandler here to keep the JARVIS terminal clean
    ]
)

logger = logging.getLogger("JARVIS-CORE")

def log_info(message):
    """Logs an informational message."""
    logger.info(message)

def log_warning(message):
    """Logs a warning message."""
    logger.warning(message)

def log_error(message):
    """Logs an error message with details."""
    logger.error(message, exc_info=True)

def log_query(query, intent, tasks):
    """Specialized logger for user interactions and DMM results."""
    logger.info(f"USER_QUERY: '{query}' | INTENT_IDENTIFIED: '{intent}' | TASKS: {tasks}")

if __name__ == "__main__":
    log_info("JARVIS Logging System initialized successfully.")
