# """Simple file-based logger for Odoo API application"""

# import os
# from datetime import datetime
# from pathlib import Path
# from typing import Optional


# class SimpleLogger:
#     """Simple file-based logger that doesn't rely on Python's logging module"""
    
#     def __init__(self, log_file: str = "logs/odoo_api.log", max_size: int = 10485760):
#         self.log_file = Path(log_file)
#         self.max_size = max_size
#         self.backup_count = 5
        
#         # Create logs directory if it doesn't exist
#         self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
#     def _rotate_if_needed(self):
#         """Rotate log file if it exceeds max size"""
#         try:
#             if self.log_file.exists() and self.log_file.stat().st_size > self.max_size:
#                 # Rotate existing backups
#                 for i in range(self.backup_count - 1, 0, -1):
#                     old_file = self.log_file.parent / f"{self.log_file.stem}.{i}{self.log_file.suffix}"
#                     new_file = self.log_file.parent / f"{self.log_file.stem}.{i+1}{self.log_file.suffix}"
#                     if old_file.exists():
#                         old_file.rename(new_file)
                
#                 # Rotate current log file
#                 backup_file = self.log_file.parent / f"{self.log_file.stem}.1{self.log_file.suffix}"
#                 if self.log_file.exists():
#                     self.log_file.rename(backup_file)
#         except Exception as e:
#             print(f"Error rotating log file: {e}")
    
#     def _write_log(self, level: str, message: str):
#         """Write a log message to file"""
#         try:
#             self._rotate_if_needed()
            
#             timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             log_entry = f"{timestamp} - {level} - {message}\n"
            
#             with open(self.log_file, 'a', encoding='utf-8') as f:
#                 f.write(log_entry)
            
#             # Also print to console
#             print(log_entry.strip())
                
#         except Exception as e:
#             print(f"Error writing to log file: {e}")
    
#     def debug(self, message: str):
#         """Log debug message"""
#         self._write_log("DEBUG", message)
    
#     def info(self, message: str):
#         """Log info message"""
#         self._write_log("INFO", message)
    
#     def warning(self, message: str):
#         """Log warning message"""
#         self._write_log("WARNING", message)
    
#     def error(self, message: str):
#         """Log error message"""
#         self._write_log("ERROR", message)


# def tail_logs(log_file: str = "logs/odoo_api.log", lines: int = 100) -> list[str]:
#     """
#     Tail the last N lines from a log file
    
#     Args:
#         log_file: Path to log file
#         lines: Number of lines to return
        
#     Returns:
#         List of log lines
#     """
#     log_path = Path(log_file)
    
#     if not log_path.exists():
#         return [f"Log file not found: {log_file}"]
    
#     try:
#         with open(log_path, 'r', encoding='utf-8') as f:
#             # Read all lines and return the last N
#             all_lines = f.readlines()
#             return all_lines[-lines:] if len(all_lines) > lines else all_lines
#     except Exception as e:
#         return [f"Error reading log file: {str(e)}"]


# def get_log_files() -> list[str]:
#     """
#     Get list of available log files
    
#     Returns:
#         List of log file paths
#     """
#     logs_dir = Path("logs")
#     if not logs_dir.exists():
#         return []
    
#     log_files = []
#     for file_path in logs_dir.glob("*.log"):
#         log_files.append(str(file_path))
    
#     return sorted(log_files)


# # Global logger instance
# logger = SimpleLogger()