"""
Global UI manager to coordinate different user interfaces and prevent conflicts.
This centralizes UI state and ensures only one UI is active at a time.
"""

import threading
import time
from debug_logger import info, warning, error, debug

# Global UI state
_state = {
    'active_ui': None,  # Name of the currently active UI
    'start_time': 0,    # When current UI was started
    'lock': threading.RLock(),  # Thread safety
    'tk_root': None,    # Current Tkinter root (main window)
    'registered_uis': {}  # Map of UI names to their window objects
}

def register_ui(ui_name, ui_window):
    """Register a UI as available
    
    Args:
        ui_name (str): Name of the UI ('splash', 'main_menu', 'emergency', etc.)
        ui_window: Tkinter window object
        
    Returns:
        bool: True if registered, False if a UI with that name already exists
    """
    with _state['lock']:
        if ui_name in _state['registered_uis']:
            return False
        
        _state['registered_uis'][ui_name] = ui_window
        debug(f"Registered UI: {ui_name}")
        return True

def unregister_ui(ui_name):
    """Unregister a UI
    
    Args:
        ui_name (str): Name of the UI to unregister
        
    Returns:
        bool: True if found and unregistered, False if not found
    """
    with _state['lock']:
        if ui_name in _state['registered_uis']:
            del _state['registered_uis'][ui_name]
            debug(f"Unregistered UI: {ui_name}")
            
            # If it was the active UI, clear that too
            if _state['active_ui'] == ui_name:
                _state['active_ui'] = None
                _state['start_time'] = 0
                _state['tk_root'] = None
            
            return True
        return False

def set_active_ui(ui_name, ui_window=None):
    """Set the active UI
    
    Args:
        ui_name (str): Name of the UI to set as active
        ui_window: Optional Tkinter window object (will be registered if not already)
        
    Returns:
        bool: True if successfully set active
    """
    with _state['lock']:
        # Register window if provided and not already registered
        if ui_window and ui_name not in _state['registered_uis']:
            _state['registered_uis'][ui_name] = ui_window
        
        # Make sure UI exists
        if ui_name not in _state['registered_uis'] and ui_name is not None:
            warning(f"Attempted to set unknown UI as active: {ui_name}")
            return False
        
        prev_ui = _state['active_ui']
        _state['active_ui'] = ui_name
        _state['start_time'] = time.time() if ui_name else 0
        
        if ui_name:
            _state['tk_root'] = _state['registered_uis'].get(ui_name)
            info(f"Set active UI: {ui_name} (previously: {prev_ui})")
        else:
            _state['tk_root'] = None
            debug(f"Cleared active UI (previously: {prev_ui})")
        
        return True

def get_active_ui():
    """Get the name of the currently active UI
    
    Returns:
        str: Name of the active UI or None if no UI is active
    """
    with _state['lock']:
        return _state['active_ui']

def get_active_window():
    """Get the window object of the currently active UI
    
    Returns:
        Window object or None if no UI is active
    """
    with _state['lock']:
        if _state['active_ui']:
            return _state['registered_uis'].get(_state['active_ui'])
        return None

def is_any_ui_active():
    """Check if any UI is currently active
    
    Returns:
        bool: True if a UI is active, False otherwise
    """
    with _state['lock']:
        return _state['active_ui'] is not None

def get_ui_uptime():
    """Get the uptime of the current UI in seconds
    
    Returns:
        float: Uptime in seconds, or 0 if no UI is active
    """
    with _state['lock']:
        if _state['active_ui'] and _state['start_time'] > 0:
            return time.time() - _state['start_time']
        return 0

def close_all_uis():
    """Attempt to close all registered UIs
    
    Returns:
        int: Number of UIs that were closed
    """
    with _state['lock']:
        closed_count = 0
        for ui_name, window in list(_state['registered_uis'].items()):
            try:
                if hasattr(window, 'destroy') and hasattr(window, 'winfo_exists'):
                    if window.winfo_exists():
                        window.destroy()
                        closed_count += 1
            except Exception as e:
                error(f"Error closing UI {ui_name}: {e}")
        
        # Clear all state
        _state['registered_uis'].clear()
        _state['active_ui'] = None
        _state['start_time'] = 0
        _state['tk_root'] = None
        
        return closed_count

def schedule_on_active_ui(func, *args, **kwargs):
    """Schedule a function to run on the active UI's thread
    
    Args:
        func: Function to run
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        bool: True if scheduled, False if no active UI
    """
    with _state['lock']:
        if _state['tk_root'] and hasattr(_state['tk_root'], 'after'):
            try:
                _state['tk_root'].after(0, lambda: func(*args, **kwargs))
                return True
            except Exception as e:
                error(f"Error scheduling on active UI: {e}")
        return False
