import customtkinter as ctk
from PIL import Image, ImageTk
import time
import os
import _tkinter  # Add explicit import for _tkinter
import threading  # Add explicit import for threading
import functools  # Add explicit import for functools

# Global UI state tracking
_ui_state = {
    'emergency_active': False,
    'main_ui_active': False,
    'ui_started_at': 0
}

def is_any_ui_active():
    """Check if any UI (normal or emergency) is currently active
    
    Returns:
        bool: True if UI is active
    """
    return _ui_state['emergency_active'] or _ui_state['main_ui_active']

def mark_emergency_active(active=True):
    """Mark the emergency UI as active or inactive
    
    Args:
        active (bool): Whether emergency UI is active
    """
    _ui_state['emergency_active'] = active
    if active:
        _ui_state['ui_started_at'] = time.time()

def mark_main_ui_active(active=True):
    """Mark the main UI as active or inactive
    
    Args:
        active (bool): Whether main UI is active
    """
    _ui_state['main_ui_active'] = active
    if active:
        _ui_state['ui_started_at'] = time.time()

def get_ui_uptime():
    """Get how long the current UI has been active
    
    Returns:
        float: Time in seconds since UI was activated, or 0 if no UI active
    """
    if is_any_ui_active():
        return time.time() - _ui_state['ui_started_at']
    return 0

def convert_to_ctk_image(pil_image, size=None):
    """Convert a PIL image to CTkImage for proper scaling on HighDPI displays
    
    Args:
        pil_image (PIL.Image): PIL image to convert
        size (tuple): Optional size to resize image to (width, height)
        
    Returns:
        CTkImage: CustomTkinter image
    """
    if size is not None:
        pil_image = pil_image.resize(size)
    
    # Create CTkImage from PIL image
    return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)

def load_gif_frames_as_ctk(filepath, size=None):
    """Load GIF frames as CTkImage objects
    
    Args:
        filepath (str): Path to GIF file
        size (tuple): Optional size to resize frames to (width, height)
        
    Returns:
        list: List of CTkImage frames
    """
    from PIL import Image, ImageSequence
    
    frames = []
    try:
        with Image.open(filepath) as img:
            for frame in ImageSequence.Iterator(img):
                # Convert frame to RGBA and resize if needed
                frame = frame.convert("RGBA")
                if size:
                    frame = frame.resize(size)
                
                # Convert to CTkImage
                ctk_frame = convert_to_ctk_image(frame)
                frames.append(ctk_frame)
    except Exception as e:
        print(f"Error loading GIF frames from {filepath}: {e}")
    
    return frames

def safe_after(widget, delay, callback):
    """Schedule a callback safely with existence checking
    
    Args:
        widget: Tkinter widget to schedule after on
        delay: Delay in milliseconds
        callback: Function to call
        
    Returns:
        after_id: ID that can be used to cancel, or None if scheduling failed
    """
    # Check if widget exists
    try:
        if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
            return None
    except _tkinter.TclError:
        # Application is being destroyed
        return None
    
    # Check if the widget's owner is closing
    if hasattr(widget, 'master') and hasattr(widget.master, 'is_closing') and widget.master.is_closing:
        return None
        
    # Create a wrapper that checks if widget still exists before executing callback
    def safe_callback():
        try:
            if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                try:
                    callback()
                except Exception as e:
                    print(f"Error in after callback: {e}")
        except _tkinter.TclError:
            # Application is being destroyed, ignore
            pass
    
    # Schedule the callback
    try:
        return widget.after(delay, safe_callback)
    except _tkinter.TclError:
        # Application is being destroyed
        return None
    except Exception as e:
        print(f"Error scheduling after callback: {e}")
        return None

def cancel_after_safely(widget, after_id):
    """Cancel an after callback safely
    
    Args:
        widget: Tkinter widget to cancel after on
        after_id: ID returned from after()
        
    Returns:
        bool: True if canceled successfully, False otherwise
    """
    if after_id is None:
        return False
    
    try:
        if hasattr(widget, 'after_cancel') and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
            widget.after_cancel(after_id)
            return True
    except Exception:
        pass
    
    return False

def safe_widget_update(widget, **kwargs):
    """Safely update a widget's properties with existence check
    
    Args:
        widget: Tkinter widget to update
        **kwargs: Configuration properties to set
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        # Check if the application is closing
        if hasattr(widget, 'master') and hasattr(widget.master, 'is_closing') and widget.master.is_closing:
            return False
            
        if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
            widget.configure(**kwargs)
            return True
        return False
    except _tkinter.TclError:
        # Application is being destroyed
        return False
    except Exception as e:
        print(f"Error updating widget: {e}")
        return False

def safe_widget_method(widget, method_name, *args, **kwargs):
    """Safely call a method on a widget with existence check
    
    Args:
        widget: Tkinter widget to call method on
        method_name: Name of method to call
        *args, **kwargs: Arguments to pass to method
        
    Returns:
        Result of method call or None if widget doesn't exist
    """
    try:
        if hasattr(widget, 'winfo_exists') and widget.winfo_exists() and hasattr(widget, method_name):
            method = getattr(widget, method_name)
            return method(*args, **kwargs)
        return None
    except Exception as e:
        print(f"Error calling method {method_name} on widget: {e}")
        return None

def ensure_ui_thread(root, callback, *args, **kwargs):
    """Ensure a callback runs on the UI thread
    
    Args:
        root: Tkinter root window
        callback: Function to call
        *args, **kwargs: Arguments to pass to callback
        
    Returns:
        after_id: ID from after() call or None if failed
    """
    try:
        if hasattr(root, 'winfo_exists') and root.winfo_exists():
            return root.after(0, lambda: callback(*args, **kwargs))
        return None
    except Exception as e:
        print(f"Error scheduling callback on UI thread: {e}")
        return None

def find_ui_root(obj):
    """Find a UI root object in an instance
    
    Args:
        obj: Object to search for UI root
        
    Returns:
        UI root object or None if not found
    """
    # Common UI object names
    for attr_name in ['window', 'root', 'master', 'app', 'frame', 'parent', 'tk', 'top']:
        if hasattr(obj, attr_name):
            ui_obj = getattr(obj, attr_name)
            if hasattr(ui_obj, 'after') and hasattr(ui_obj, 'winfo_exists'):
                if ui_obj.winfo_exists():
                    return ui_obj
    
    # Also try checking if the object itself is a UI object
    if hasattr(obj, 'after') and hasattr(obj, 'winfo_exists') and obj.winfo_exists():
        return obj
        
    return None

def cleanup_after_commands():
    """Clean up invalid Tkinter after commands
    
    This helps prevent "invalid command name" errors that can occur
    when the application is shutting down or switching between windows.
    """
    try:
        # Get the root Tk instance
        from tkinter import _default_root
        if _default_root:
            # Get all after commands
            after_ids = _default_root.tk.call('after', 'info')
            
            # Convert to Python list
            if isinstance(after_ids, str):
                after_ids = after_ids.split()
            
            # Cancel all after commands
            for after_id in after_ids:
                try:
                    _default_root.after_cancel(after_id)
                except Exception:
                    # If can't cancel, just continue
                    pass
    except Exception as e:
        print(f"Error cleaning up after commands: {e}")

def ensure_ctk_images(images):
    """Ensure all images in a collection are CTkImages
    
    Args:
        images: List, tuple or dictionary of images
        
    Returns:
        Same collection with all PIL images converted to CTkImage
    """
    try:
        if isinstance(images, list):
            return [_ensure_single_ctk_image(img) for img in images]
        elif isinstance(images, tuple):
            return tuple(_ensure_single_ctk_image(img) for img in images)
        elif isinstance(images, dict):
            return {k: _ensure_single_ctk_image(v) for k, v in images.items()}
        else:
            return _ensure_single_ctk_image(images)
    except Exception as e:
        print(f"Error ensuring CTkImages: {e}")
        return images
        
def _ensure_single_ctk_image(image):
    """Convert a single image to CTkImage if needed
    
    Args:
        image: Image object
        
    Returns:
        CTkImage if conversion needed and possible, otherwise original image
    """
    if image is None:
        return None
        
    # If it's already a CTkImage, return as is
    if isinstance(image, ctk.CTkImage):
        return image
        
    # If it's a PIL.ImageTk.PhotoImage, convert from the original PIL image if possible
    if isinstance(image, ImageTk.PhotoImage):
        if hasattr(image, 'pil_image'):
            return convert_to_ctk_image(image.pil_image)
        # Can't recover original PIL image, return as is
        return image
        
    # If it's a PIL.Image, convert it
    if hasattr(image, 'mode'):  # Simple check for PIL.Image
        return convert_to_ctk_image(image)
        
    # Can't convert, return as is
    return image

def apply_window_transition(old_window, new_window, fade_duration=300):
    """Apply a smooth transition between two windows
    
    Args:
        old_window: Window to fade out and close
        new_window: Window to fade in
        fade_duration (int): Total duration of transition in milliseconds
        
    Returns:
        bool: True if transition started successfully
    """
    try:
        # Check if both windows exist
        if not hasattr(old_window, 'winfo_exists') or not old_window.winfo_exists() or \
           not hasattr(new_window, 'winfo_exists') or not new_window.winfo_exists():
            return False
        
        # Position new window at same location as old window
        x = old_window.winfo_x()
        y = old_window.winfo_y()
        new_window.geometry(f"+{x}+{y}")
        
        # Set initial transparency
        old_window.attributes("-alpha", 1.0)
        new_window.attributes("-alpha", 0.0)
        
        # Prepare new window but keep it hidden
        new_window.update_idletasks()
        
        # Calculate step size and delay
        steps = 10
        step_time = fade_duration // steps
        alpha_step = 1.0 / steps
        
        # Start the transition
        _run_transition_step(old_window, new_window, 0, steps, alpha_step, step_time)
        return True
        
    except Exception as e:
        print(f"Error setting up window transition: {e}")
        return False

def _run_transition_step(old_window, new_window, step, total_steps, alpha_step, step_time):
    """Run a single step of the window transition
    
    Args:
        old_window: Window to fade out
        new_window: Window to fade in
        step (int): Current step number
        total_steps (int): Total number of steps
        alpha_step (float): Alpha change per step
        step_time (int): Time per step in milliseconds
    """
    try:
        # Calculate alpha values
        old_alpha = max(1.0 - step * alpha_step, 0.0)
        new_alpha = min(step * alpha_step, 1.0)
        
        # Update window transparencies
        if hasattr(old_window, 'winfo_exists') and old_window.winfo_exists():
            old_window.attributes("-alpha", old_alpha)
        
        # If we're at the halfway point, make new window visible
        if step == total_steps // 2:
            if hasattr(new_window, 'winfo_exists') and new_window.winfo_exists():
                new_window.deiconify()
                new_window.update_idletasks()
        
        # Update new window if it's visible
        if step >= total_steps // 2:
            if hasattr(new_window, 'winfo_exists') and new_window.winfo_exists():
                new_window.attributes("-alpha", new_alpha)
                
                # Ensure new window is in front
                new_window.lift()
        
        # Schedule next step or finish
        if step < total_steps:
            if hasattr(new_window, 'winfo_exists') and new_window.winfo_exists():
                new_window.after(step_time, lambda: _run_transition_step(
                    old_window, new_window, step + 1, total_steps, alpha_step, step_time))
        else:
            # Finalize transition
            if hasattr(old_window, 'winfo_exists') and old_window.winfo_exists():
                old_window.withdraw()
                old_window.destroy()
            
            if hasattr(new_window, 'winfo_exists') and new_window.winfo_exists():
                new_window.attributes("-alpha", 1.0)
                new_window.focus_force()
    
    except Exception as e:
        print(f"Error during transition step: {e}")
        
        # Try to ensure windows are in a usable state
        try:
            if hasattr(old_window, 'winfo_exists') and old_window.winfo_exists():
                old_window.withdraw()
            
            if hasattr(new_window, 'winfo_exists') and new_window.winfo_exists():
                new_window.deiconify()
                new_window.attributes("-alpha", 1.0)
                new_window.focus_force()
        except:
            pass

def is_main_thread():
    """Check if the current thread is the main thread
    
    Returns:
        bool: True if current thread is main thread
    """
    return threading.current_thread() is threading.main_thread()

def safe_tk_call(widget, func, *args, **kwargs):
    """Safely call a Tkinter function that must run on main thread
    
    Args:
        widget: Tkinter widget to use for scheduling
        func: Function to call (usually a method of the widget)
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Result of function call or None if it couldn't be called safely
    """
    # If we're on the main thread, call directly
    if is_main_thread():
        try:
            if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                return func(*args, **kwargs)
        except _tkinter.TclError as e:
            if "application has been destroyed" in str(e):
                print("Widget has been destroyed, skipping operation")
            else:
                print(f"Tkinter error: {e}")
        except Exception as e:
            print(f"Error in Tkinter operation: {e}")
    else:
        # We're in a background thread, need to schedule on main thread
        try:
            if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                # Create a simple Future-like object to get the result
                result_holder = {'result': None, 'done': False, 'error': None}
                
                def main_thread_func():
                    try:
                        result_holder['result'] = func(*args, **kwargs)
                    except Exception as e:
                        result_holder['error'] = e
                    finally:
                        result_holder['done'] = True
                
                widget.after(0, main_thread_func)
                
                # Can't wait for result in background thread without blocking
                # So just return None - caller needs to handle async behavior
                return None
        except:
            # Ignore errors about widget not existing
            pass
    
    return None

def thread_safe_ui_update(root, update_func, *args, **kwargs):
    """Update UI in a thread-safe way
    
    Args:
        root: Tkinter root object
        update_func: Function to update UI
        *args, **kwargs: Arguments to pass to update function
    """
    if is_main_thread():
        # In main thread, call directly
        try:
            if hasattr(root, 'winfo_exists') and root.winfo_exists():
                update_func(*args, **kwargs)
        except Exception as e:
            print(f"Error in UI update: {e}")
    else:
        # In background thread, schedule on main thread
        try:
            if hasattr(root, 'winfo_exists') and root.winfo_exists():
                root.after(0, lambda: update_func(*args, **kwargs))
        except Exception as e:
            print(f"Error scheduling UI update: {e}")

def thread_safe_window_check(window):
    """Check if a window exists in a thread-safe way
    
    Args:
        window: Tkinter window to check
    
    Returns:
        bool: True if window exists and is valid, False otherwise
    """
    # Must be on main thread for winfo_exists to work
    if not is_main_thread():
        return False
        
    try:
        return hasattr(window, 'winfo_exists') and window.winfo_exists()
    except Exception:
        return False

def schedule_on_main_thread(root, func, *args, **kwargs):
    """Schedule a function to run on the main thread
    
    Args:
        root: Tkinter root/window
        func: Function to run
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        bool: True if scheduled, False otherwise
    """
    try:
        if thread_safe_window_check(root):
            root.after(0, lambda: func(*args, **kwargs))
            return True
        return False
    except Exception as e:
        print(f"Error scheduling on main thread: {e}")
        return False

def run_on_main_thread(func):
    """Decorator to ensure a function only runs on the main thread
    
    If the function is called from a background thread, it's ignored.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that only runs on main thread
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            return func(*args, **kwargs)
        else:
            func_name = getattr(func, "__name__", str(func))
            print(f"Warning: {func_name} called from background thread - ignoring")
            return None
    return wrapper

def detect_deadlock():
    """Check for potential deadlocks in the application
    
    Returns:
        bool: True if potential deadlock detected
    """
    import threading
    
    # Get all threads
    threads = threading.enumerate()
    
    # Look for suspicious thread states
    blocked_threads = []
    for thread in threads:
        # Skip daemon threads
        if thread.daemon:
            continue
            
        # Check if the thread is alive and not the main thread
        if thread.is_alive() and thread is not threading.main_thread():
            blocked_threads.append(thread.name)
    
    # If we have blocked non-daemon threads, might be a deadlock
    if blocked_threads:
        print(f"POTENTIAL DEADLOCK DETECTED. Blocked threads: {blocked_threads}")
        
        # Print thread stack traces for debugging
        import traceback
        import sys
        
        for thread_id, frame in sys._current_frames().items():
            thread_name = None
            for t in threads:
                if t.ident == thread_id:
                    thread_name = t.name
                    break
                    
            if thread_name:
                print(f"\nThread {thread_name} ({thread_id}):")
                traceback.print_stack(frame)
                
        return True
        
    return False

# Global application heartbeat tracking
_app_heartbeat = {
    'last_beat': time.time(),
    'counter': 0
}

def update_app_heartbeat():
    """Update the application heartbeat timestamp
    
    Returns:
        int: New heartbeat counter value
    """
    _app_heartbeat['last_beat'] = time.time()
    _app_heartbeat['counter'] += 1
    return _app_heartbeat['counter']

def get_time_since_last_heartbeat():
    """Get time since the last heartbeat
    
    Returns:
        float: Time in seconds since last heartbeat
    """
    return time.time() - _app_heartbeat['last_beat']

def force_exit_if_stuck(timeout=30):
    """Schedule a force exit if the application appears to be stuck
    
    Args:
        timeout: Seconds to wait before forcing exit
        
    Returns:
        threading.Thread: Monitor thread object
    """
    import threading
    import time
    import os
    import sys
    from debug_logger import warning, error, info, debug
    
    def monitor_thread():
        debug(f"Starting force exit monitor with {timeout}s timeout")
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            
            # Check heartbeat first - if it's been updated recently, reset the timer
            time_since_heartbeat = get_time_since_last_heartbeat()
            if time_since_heartbeat < 10.0:  # If heartbeat within last 10 seconds
                debug(f"Heartbeat detected ({time_since_heartbeat:.1f}s ago), resetting monitor timeout")
                start_time = time.time()  # Reset the timer
            
            # Check if any UI is active and responsive
            if is_any_ui_active() and get_ui_uptime() > 5.0:
                # UI has been active for at least 5 seconds, probably not stuck
                # Extend the timeout period or reset it
                start_time = time.time()  # Reset the timer
            
            # Check if we've exceeded the timeout
            if elapsed > timeout:
                warning(f"\n\nFORCE EXIT: Application appears to be stuck for {timeout} seconds.")
                if detect_deadlock():
                    error("Deadlock detected. Forcing process termination.")
                else:
                    warning("No obvious deadlock but application is unresponsive. Forcing exit.")
                
                # Try to flush logs before exiting
                sys.stdout.flush()
                sys.stderr.flush()
                
                # Force terminate process
                os._exit(1)
                
            # Sleep for a bit before checking again
            time.sleep(1)
    
    # Start monitoring in a daemon thread
    monitor = threading.Thread(target=monitor_thread, daemon=True)
    monitor.name = "ForceExitMonitor"
    monitor.start()
    print(f"Started force exit monitor with {timeout} second timeout")
    return monitor

def force_early_timeout(max_init_time=10, emergency_callback=None):
    """Set a timeout for early initialization to prevent hangs during startup
    
    This creates a daemon thread that will monitor the initialization process
    and force a process exit if it takes too long to get to the splash screen.
    
    Args:
        max_init_time (int): Maximum time in seconds allowed for initialization
        emergency_callback (callable): Function to call for emergency recovery
    """
    import threading
    import time
    import os
    import sys
    from debug_logger import warning, error, info
    
    def monitor_early_init():
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            # Check if any UI is already active
            if is_any_ui_active():
                ui_uptime = get_ui_uptime()
                if ui_uptime > 2.0:  # If UI has been active for at least 2 seconds
                    info(f"Early timeout monitor detected active UI for {ui_uptime:.1f}s, stopping monitoring")
                    return  # UI is active and running, so we can stop monitoring
            
            # Check for timeout if no UI is successfully running
            if elapsed > max_init_time and not is_any_ui_active():
                error(f"\n\nEARLY TIMEOUT: Application took too long ({max_init_time}s) to initialize.")
                warning("This may be caused by a CustomTkinter or tkinter issue.")
                
                # Only proceed with emergency if no UI is active yet
                if not is_any_ui_active():
                    # Call emergency callback if provided
                    if emergency_callback and callable(emergency_callback):
                        warning("Attempting emergency recovery...")
                        try:
                            # Run in main thread if possible
                            if threading.current_thread() is threading.main_thread():
                                mark_emergency_active(True)
                                emergency_callback()
                            else:
                                # Try to schedule on main thread via tkinter if available
                                try:
                                    import tkinter
                                    if hasattr(tkinter, '_default_root') and tkinter._default_root:
                                        info("Scheduling emergency recovery on main thread")
                                        mark_emergency_active(True)
                                        tkinter._default_root.after(0, emergency_callback)
                                        # Don't exit process, let callback run
                                        return
                                except:
                                    # If can't schedule on main thread, try direct call
                                    warning("Couldn't schedule on main thread, trying direct call")
                                    mark_emergency_active(True)
                                    emergency_callback()
                        except Exception as e:
                            error(f"Emergency callback failed: {e}")
                            mark_emergency_active(False)  # Reset flag
                else:
                    info("UI already active, skipping emergency recovery")
                    return

                # Only exit if no UI got activated
                if not is_any_ui_active():
                    warning("Attempting to exit cleanly (no UI was started)...")
                    
                    # Try to flush logs
                    sys.stdout.flush()
                    sys.stderr.flush()
                    
                    # Exit process
                    os._exit(1)
            
            # Check frequently at first, then less often
            time.sleep(0.5)
    
    # Start the monitoring thread as daemon
    monitoring_thread = threading.Thread(target=monitor_early_init, daemon=True)
    monitoring_thread.name = "EmergencyTimeoutMonitor"
    monitoring_thread.start()
    
    # Create a fallback timer with signal
    try:
        import signal
        def timeout_handler(signum, frame):
            # Only act if no UI is active yet
            if not is_any_ui_active():
                error("\n\nSIGNAL TIMEOUT: Early initialization timed out")
                
                # Try emergency callback here too if available
                if emergency_callback and callable(emergency_callback) and not is_any_ui_active():
                    try:
                        mark_emergency_active(True)
                        emergency_callback()
                    except Exception:
                        mark_emergency_active(False)
                        pass
            else:
                info("Signal timeout triggered but UI already active, ignoring")
        
        # Set 30-second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
    except (ImportError, AttributeError):
        # signal.SIGALRM not available on this platform
        pass

def safe_ctk_window_init(window_class, *args, timeout=5.0, **kwargs):
    """Safely initialize a CustomTkinter window with timeout protection
    
    Args:
        window_class: CustomTkinter window class to instantiate
        timeout: Seconds to wait before giving up
        *args, **kwargs: Arguments to pass to window class
        
    Returns:
        The initialized window object or None if failed
    """
    import time
    import threading
    from debug_logger import warning, error, debug
    
    # Create event to signal completion
    init_complete = threading.Event()
    result = [None]
    error_info = [None]
    
    # Function to execute in main thread
    def init_window():
        try:
            debug(f"Initializing {window_class.__name__}")
            window = window_class(*args, **kwargs)
            result[0] = window
        except Exception as e:
            error(f"Error initializing {window_class.__name__}: {e}")
            error_info[0] = str(e)
            import traceback
            traceback.print_exc()
        finally:
            init_complete.set()
    
    # If we're already in main thread, call directly
    if threading.current_thread() is threading.main_thread():
        init_window()
        return result[0]
    
    # Otherwise schedule on main thread
    try:
        # Find an existing Tkinter root
        import tkinter
        if hasattr(tkinter, '_default_root') and tkinter._default_root:
            tkinter._default_root.after(0, init_window)
        else:
            # Create a temporary root for initialization
            temp_root = tkinter.Tk()
            temp_root.withdraw()
            temp_root.after(0, init_window)
            temp_root.after(int(timeout * 1000) + 100, temp_root.destroy)
            temp_root.mainloop()
    except Exception as e:
        error(f"Error scheduling window initialization: {e}")
        return None
    
    # Wait for initialization with timeout
    start_time = time.time()
    while not init_complete.is_set() and time.time() - start_time < timeout:
        time.sleep(0.05)
    
    if not init_complete.is_set():
        warning(f"Timeout waiting for {window_class.__name__} initialization")
        return None
    
    if error_info[0]:
        warning(f"Window initialization had error: {error_info[0]}")
    
    return result[0]

def detect_ui_deadlock(window, timeout=5.0):
    """Check if the UI thread appears to be deadlocked
    
    Args:
        window: Tkinter window to check
        timeout: Maximum time in seconds to wait for response
        
    Returns:
        bool: True if UI thread appears to be deadlocked
    """
    from debug_logger import debug, warning
    import threading
    import time
    
    # Only run this check from a non-main thread
    if threading.current_thread() is threading.main_thread():
        return False
    
    # Flag to indicate if the window responded
    responded = [False]
    
    # Function to run in the UI thread
    def ui_response_check():
        responded[0] = True
    
    # Try to schedule the function on the UI thread
    try:
        if thread_safe_window_check(window):
            window.after(0, ui_response_check)
        else:
            # Window doesn't exist
            return False
    except Exception as e:
        warning(f"Could not schedule UI response check: {e}")
        return True  # Consider it deadlocked if we can't even schedule
    
    # Wait for the UI thread to run our function
    start_time = time.time()
    while not responded[0] and time.time() - start_time < timeout:
        time.sleep(0.1)
    
    if not responded[0]:
        warning(f"UI thread did not respond within {timeout} seconds")
        return True
    
    debug("UI thread responded to deadlock check")
    return False

def unstick_ui_thread(window):
    """Attempt to unstick a deadlocked UI thread
    
    Args:
        window: Tkinter window to unstick
        
    Returns:
        bool: True if unstick attempt was made, False otherwise
    """
    from debug_logger import info, warning, error
    import threading
    
    # Only run from non-main thread
    if threading.current_thread() is threading.main_thread():
        warning("Cannot unstick UI thread from main thread")
        return False
    
    # First try to detect if the UI thread is actually deadlocked
    if not detect_ui_deadlock(window):
        info("UI thread is not deadlocked, no need to unstick")
        return False
    
    warning("Attempting to unstick UI thread")
    
    # Try various recovery approaches
    try:
        # 1. Try to force window focus which might process events
        info("Trying to force window focus")
        window.after(0, lambda: window.focus_force())
        
        # 2. Wait a moment and check if that worked
        import time
        time.sleep(0.5)
        if not detect_ui_deadlock(window):
            info("UI thread unstuck by forcing focus")
            return True
            
        # 3. Try to process pending events
        warning("Focus approach failed, trying to force event processing")
        window.after(0, lambda: window.update())
        time.sleep(0.5)
        if not detect_ui_deadlock(window):
            info("UI thread unstuck by forcing update")
            return True
            
        # 4. Last resort - try to restart the window
        warning("Standard approaches failed, attempting to restart window")
        # This is risky and application-specific
        # Implementation would depend on how your app can restart windows
        return False
        
    except Exception as e:
        error(f"Error attempting to unstick UI thread: {e}")
        return False
