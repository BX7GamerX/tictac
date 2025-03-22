"""
Debug logger for the Tic Tac Toe application.
Provides consistent logging with timestamps and optional console colors.
"""

import datetime
import threading
import inspect
import os

# ANSI color codes for terminal output
COLORS = {
    'RESET': '\033[0m',
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'PURPLE': '\033[95m',
    'CYAN': '\033[96m',
    'WHITE': '\033[97m',
}

# Set to True to enable file logging
LOG_TO_FILE = True
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "app_debug.log")

# Create/clear the log file on startup
if LOG_TO_FILE:
    with open(LOG_FILE_PATH, 'w') as f:
        f.write(f"=== Tic Tac Toe Debug Log - Started {datetime.datetime.now()} ===\n\n")

def log(message, level="INFO", color=None):
    """
    Log a message with timestamp, thread info, and optional color.
    
    Args:
        message (str): Message to log
        level (str): Log level (INFO, WARNING, ERROR, DEBUG)
        color (str): Color name from COLORS dict
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    is_main = "MAIN" if threading.current_thread() is threading.main_thread() else "BG"
    
    # Get the caller's module and function
    caller_frame = inspect.currentframe().f_back
    if caller_frame:
        caller_module = caller_frame.f_globals.get('__name__', 'unknown')
        caller_function = caller_frame.f_code.co_name
        location = f"{caller_module}.{caller_function}"
    else:
        location = "unknown"
    
    # Format the log message
    formatted_msg = f"[{timestamp}] [{level}] [{is_main}:{thread_name}] [{location}] {message}"
    
    # Apply colors for terminal if specified
    if color and color in COLORS:
        terminal_msg = f"{COLORS[color]}{formatted_msg}{COLORS['RESET']}"
    else:
        terminal_msg = formatted_msg
    
    # Print to console
    print(terminal_msg)
    
    # Write to log file if enabled
    if LOG_TO_FILE:
        try:
            with open(LOG_FILE_PATH, 'a') as f:
                f.write(formatted_msg + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")

def info(message):
    """Log an info message"""
    log(message, "INFO", "WHITE")

def warning(message):
    """Log a warning message"""
    log(message, "WARNING", "YELLOW")

def error(message):
    """Log an error message"""
    log(message, "ERROR", "RED")

def debug(message):
    """Log a debug message"""
    log(message, "DEBUG", "CYAN")

def success(message):
    """Log a success message"""
    log(message, "SUCCESS", "GREEN")

# Function for logging transition events specifically
def transition(message):
    """Log a transition event"""
    log(message, "TRANSITION", "PURPLE")
