import threading
import queue
import traceback
import time
from functools import wraps

class ThreadedTaskManager:
    """Manager for handling background tasks with proper thread synchronization
    
    This class provides a simple API for running tasks in background threads
    while ensuring UI updates happen on the main thread.
    """
    
    def __init__(self):
        """Initialize the task manager"""
        self.tasks = {}  # Track ongoing tasks
        self.tasks_lock = threading.RLock()  # Thread-safe access to tasks
        self.result_queue = queue.Queue()  # Queue for returning results to main thread
        self.running = True
        
        # Start worker threads
        self.worker_threads = []
        for i in range(2):  # Create 2 worker threads
            thread = threading.Thread(target=self._result_processor, daemon=True)
            thread.start()
            self.worker_threads.append(thread)
    
    def run_in_background(self, task_func, callback=None, error_callback=None, *args, **kwargs):
        """Run a function in a background thread
        
        Args:
            task_func: Function to run in background
            callback: Function to call with result (on main thread)
            error_callback: Function to call on error (on main thread)
            *args, **kwargs: Arguments to pass to task_func
            
        Returns:
            task_id: ID of the task (can be used to cancel)
        """
        task_id = id(task_func) + int(time.time() * 1000)  # Unique ID
        
        def task_wrapper():
            try:
                # Run the task
                result = task_func(*args, **kwargs)
                
                # If callback provided, queue result for main thread
                if callback:
                    self.result_queue.put(('success', task_id, result, callback))
                
                # Clean up task record
                with self.tasks_lock:
                    if task_id in self.tasks:
                        del self.tasks[task_id]
                
                return result
            except Exception as e:
                # Handle error
                print(f"Error in background task: {e}")
                traceback.print_exc()
                
                # If error callback provided, queue error for main thread
                if error_callback:
                    self.result_queue.put(('error', task_id, e, error_callback))
                
                # Clean up task record
                with self.tasks_lock:
                    if task_id in self.tasks:
                        del self.tasks[task_id]
        
        # Create and start thread
        thread = threading.Thread(target=task_wrapper, daemon=True)
        
        # Store task info
        with self.tasks_lock:
            self.tasks[task_id] = {
                'thread': thread,
                'func': task_func,
                'start_time': time.time()
            }
        
        # Start the thread
        thread.start()
        
        return task_id
    
    def cancel_task(self, task_id):
        """Request cancellation of a task
        
        Note: This doesn't actually stop the thread (Python can't do that safely),
        but sets a flag that the task can check to exit early.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            bool: True if task was found and marked for cancellation
        """
        with self.tasks_lock:
            if task_id in self.tasks:
                self.tasks[task_id]['cancelled'] = True
                return True
        return False
    
    def is_task_cancelled(self, task_id):
        """Check if a task has been requested to cancel
        
        Args:
            task_id: ID of task to check
            
        Returns:
            bool: True if task should be cancelled
        """
        with self.tasks_lock:
            if task_id in self.tasks:
                return self.tasks[task_id].get('cancelled', False)
        return False
    
    def _result_processor(self):
        """Worker thread that processes results and calls callbacks on main thread"""
        while self.running:
            try:
                # Get next result from queue (blocks until available)
                result_type, task_id, result, callback = self.result_queue.get(timeout=0.5)
                
                # Process result
                if result_type == 'success':
                    # Call success callback with better error handling
                    try:
                        # Skip callback if it's a method of an object with is_closing=True
                        if hasattr(callback, '__self__') and hasattr(callback.__self__, 'is_closing'):
                            if callback.__self__.is_closing:
                                print("Skipping callback for closing application")
                                continue
                        
                        callback(result)
                    except _tkinter.TclError as e:
                        if "application has been destroyed" in str(e) or "can't invoke" in str(e):
                            print("Skipping callback - application has been destroyed")
                        else:
                            print(f"Tkinter error in callback: {e}")
                    except Exception as e:
                        print(f"Error in success callback: {e}")
                        traceback.print_exc()
                elif result_type == 'error':
                    # Call error callback with better error handling
                    try:
                        # Skip callback if it's a method of an object with is_closing=True
                        if hasattr(callback, '__self__') and hasattr(callback.__self__, 'is_closing'):
                            if callback.__self__.is_closing:
                                print("Skipping error callback for closing application")
                                continue
                        
                        callback(result)
                    except _tkinter.TclError as e:
                        if "application has been destroyed" in str(e) or "can't invoke" in str(e):
                            print("Skipping error callback - application has been destroyed")
                        else:
                            print(f"Tkinter error in error callback: {e}")
                    except Exception as e:
                        print(f"Error in error callback: {e}")
                        traceback.print_exc()
                
                # Mark task as done
                self.result_queue.task_done()
            except queue.Empty:
                # No results in queue, just continue
                continue
            except Exception as e:
                print(f"Error processing task result: {e}")
                traceback.print_exc()

    def shutdown(self):
        """Shut down the task manager"""
        self.running = False
        
        # Clear the result queue to prevent further callbacks
        try:
            while not self.result_queue.empty():
                self.result_queue.get(block=False)
                self.result_queue.task_done()
        except:
            pass
        
        # Wait for worker threads to exit
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Clear task references
        with self.tasks_lock:
            self.tasks.clear()

    @staticmethod
    def ui_safe(func):
        """Decorator to ensure a function is called on the main thread
        
        This is implemented by checking if we're on the main thread, and if not,
        scheduling the function to run on the main thread using after().
        
        Usage:
            @ThreadedTaskManager.ui_safe
            def update_ui(self, result):
                # This will always run on the main thread
                self.label.configure(text=str(result))
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check if the application is closing or already closed
            if hasattr(self, 'is_closing') and self.is_closing:
                print(f"Skipping UI update for {func.__name__} - application is closing")
                return None
                
            # Check if we're on the main thread
            if threading.current_thread() is threading.main_thread():
                # If so, just call the function directly
                try:
                    return func(self, *args, **kwargs)
                except _tkinter.TclError as e:
                    if "application has been destroyed" in str(e) or "can't invoke" in str(e):
                        print(f"Can't update UI - application has been destroyed")
                    else:
                        print(f"Tkinter error in UI update: {e}")
                    return None
            else:
                # Check for window/root UI objects to schedule on
                ui_object = None
                
                # Try different common UI object names
                for attr_name in ['window', 'root', 'master', 'app', 'frame', 'parent']:
                    if hasattr(self, attr_name):
                        obj = getattr(self, attr_name)
                        if hasattr(obj, 'after') and hasattr(obj, 'winfo_exists'):
                            try:
                                if obj.winfo_exists():
                                    ui_object = obj
                                    break
                            except _tkinter.TclError:
                                # Window was destroyed
                                continue
                
                if ui_object:
                    try:
                        # Schedule on the UI thread
                        ui_object.after(0, lambda: func(self, *args, **kwargs))
                    except _tkinter.TclError:
                        # Window was destroyed, ignore
                        pass
                else:
                    # Log the warning with better context
                    class_name = self.__class__.__name__ if hasattr(self, '__class__') else 'Unknown'
                    print(f"Warning: Can't schedule {func.__name__} on main thread for {class_name}, no valid UI object found")
                    # Don't call directly as fallback if we're in a background thread
                    return None
        return wrapper

# Global instance that can be imported and used anywhere
task_manager = ThreadedTaskManager()

def run_in_background(task_func, callback=None, error_callback=None, *args, **kwargs):
    """Convenience function to run a task in the background
    
    Args:
        task_func: Function to run in background
        callback: Function to call with result (on main thread)
        error_callback: Function to call on error (on main thread)
        *args, **kwargs: Arguments to pass to task_func
        
    Returns:
        task_id: ID of the task (can be used to cancel)
    """
    return task_manager.run_in_background(task_func, callback, error_callback, *args, **kwargs)
