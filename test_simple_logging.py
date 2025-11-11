"""Test script for simple logging functionality"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.simple_logger import logger, tail_logs, get_log_files


def test_logging():
    """Test the simple logging functionality"""
    print("Testing simple logging system...")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✓ Log messages written successfully")
    
    # Test tail functionality
    log_lines = tail_logs(lines=5)
    print(f"✓ Tail function returned {len(log_lines)} lines")
    
    # Test getting log files
    log_files = get_log_files()
    print(f"✓ Found {len(log_files)} log files: {log_files}")
    
    print("\nSimple logging system test completed successfully!")


if __name__ == "__main__":
    test_logging()