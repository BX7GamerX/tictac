"""
Patch for CustomTkinter to make it more thread-safe.
This resolves the "main thread is not in main loop" errors
that happen when customtkinter tries to check window state from a background thread.
"""

import threading
import functools
import sys
import inspect

def apply_customtkinter_patches():
    """
    Apply monkey patches to make CustomTkinter more thread-safe.
    Call this before creating any CustomTkinter widgets.
    """
    try:
        # Import the scaling tracker
        import customtkinter
        print(f"CustomTkinter version: {customtkinter.__version__}")
        
        # DIRECT APPROACH: Directly patch tkinter's callback mechanism
        # This is more reliable than trying to patch individual methods
        try:
            import tkinter
            original_call = tkinter.CallWrapper.__call__
            
            @functools.wraps(original_call)
            def thread_safe_call(self, *args):
                if threading.current_thread() is not threading.main_thread():
                    print("WARNING: Tkinter callback attempted from non-main thread - ignoring")
                    return None
                return original_call(self, *args)
            
            # Apply the patch
            tkinter.CallWrapper.__call__ = thread_safe_call
            print("Applied thread-safety patch to tkinter.CallWrapper.__call__")
        except Exception as e:
            print(f"Could not patch tkinter.CallWrapper: {e}")
        
        # CLASSIC APPROACH: Try to patch specific scaling tracker methods
        try:
            # Try first path (newer CustomTkinter versions)
            try:
                from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker
                
                # Detect if method is static or instance based on source inspection
                method_src = inspect.getsource(ScalingTracker.check_dpi_scaling)
                is_static = '@staticmethod' in method_src or '@classmethod' in method_src
                is_class = '@classmethod' in method_src
                
                if is_static and not is_class:
                    # If it's a static method, it takes no self or cls
                    original_check_dpi = ScalingTracker.check_dpi_scaling
                    
                    @staticmethod
                    @functools.wraps(original_check_dpi)
                    def thread_safe_check_dpi(*args, **kwargs):
                        if threading.current_thread() is threading.main_thread():
                            return original_check_dpi(*args, **kwargs)
                        return None
                    
                elif is_class:
                    # If it's a class method, it takes cls as first arg
                    original_check_dpi = ScalingTracker.check_dpi_scaling
                    
                    @classmethod
                    @functools.wraps(original_check_dpi)
                    def thread_safe_check_dpi(cls, *args, **kwargs):
                        if threading.current_thread() is threading.main_thread():
                            return original_check_dpi(cls, *args, **kwargs)
                        return None
                else:
                    # If it's an instance method, it takes self as first arg
                    original_check_dpi = ScalingTracker.check_dpi_scaling
                    
                    @functools.wraps(original_check_dpi)
                    def thread_safe_check_dpi(self, *args, **kwargs):
                        if threading.current_thread() is threading.main_thread():
                            return original_check_dpi(self, *args, **kwargs)
                        return None
                
                # Apply the patch
                ScalingTracker.check_dpi_scaling = thread_safe_check_dpi
                print(f"Applied thread-safety patch to ScalingTracker.check_dpi_scaling (is_static={is_static}, is_class={is_class})")
                
                # Try to similarly patch other methods
                if hasattr(ScalingTracker, 'update_scaling_callbacks'):
                    original_update = ScalingTracker.update_scaling_callbacks
                    update_is_instance_method = not inspect.ismethod(original_update) or not getattr(original_update, '__self__', None)
                    
                    if update_is_instance_method:
                        @functools.wraps(original_update)
                        def thread_safe_update(self, *args, **kwargs):
                            if threading.current_thread() is threading.main_thread():
                                return original_update(self, *args, **kwargs)
                            return None
                    else:
                        @classmethod
                        @functools.wraps(original_update)
                        def thread_safe_update(cls, *args, **kwargs):
                            if threading.current_thread() is threading.main_thread():
                                return original_update(*args, **kwargs)
                            return None
                    
                    ScalingTracker.update_scaling_callbacks = thread_safe_update
                    print("Applied thread-safety patch to update_scaling_callbacks")
            except Exception as e:
                print(f"Error patching modern ScalingTracker: {e}")
                
                # Try older version path as fallback
                try:
                    from customtkinter.scaling_tracker import ScalingTracker as OldScalingTracker
                    
                    original_check_dpi = OldScalingTracker.check_dpi_scaling
                    check_dpi_is_instance_method = not inspect.ismethod(original_check_dpi) or not getattr(original_check_dpi, '__self__', None)
                    
                    if check_dpi_is_instance_method:
                        @functools.wraps(original_check_dpi)
                        def thread_safe_check_dpi(self, *args, **kwargs):
                            if threading.current_thread() is threading.main_thread():
                                return original_check_dpi(self, *args, **kwargs)
                            return None
                    else:
                        @classmethod
                        @functools.wraps(original_check_dpi)
                        def thread_safe_check_dpi(cls, *args, **kwargs):
                            if threading.current_thread() is threading.main_thread():
                                return original_check_dpi(*args, **kwargs)
                            return None
                    
                    OldScalingTracker.check_dpi_scaling = thread_safe_check_dpi
                    print("Applied thread-safety patch to CustomTkinter DPI scaling (older version)")
                except Exception as e2:
                    print(f"Error patching older ScalingTracker: {e2}")
        
        except Exception as e:
            print(f"Error in patching ScalingTracker: {e}")
        
        # FALLBACK: Apply generic patches to all suspicious methods
        try:
            patched_count = 0
            
            # Define the wrapper generator for different method types
            def make_thread_safe_wrapper(func, is_method=True):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    if threading.current_thread() is threading.main_thread():
                        return func(*args, **kwargs)
                    return None
                return wrapper
            
            # Try to detect and patch scaling/DPI related methods in customtkinter
            for name in dir(customtkinter):
                if "scale" in name.lower() or "dpi" in name.lower():
                    try:
                        attr = getattr(customtkinter, name)
                        if callable(attr):
                            wrapped = make_thread_safe_wrapper(attr, False)
                            setattr(customtkinter, name, wrapped)
                            patched_count += 1
                    except Exception:
                        pass
            
            if patched_count > 0:
                print(f"Applied generic thread-safety patches to {patched_count} CustomTkinter methods")
                
        except Exception as e:
            print(f"Error applying generic patches: {e}")
        
        # Apply a global try/except wrapper to all tkinter operations
        try:
            # Find the _tkinter module (the C extension)
            import _tkinter
            
            # Try to patch the tcl call mechanism
            if hasattr(_tkinter, "tcl_call"):
                original_tcl_call = _tkinter.tcl_call
                
                @functools.wraps(original_tcl_call)
                def safe_tcl_call(*args, **kwargs):
                    try:
                        if threading.current_thread() is not threading.main_thread():
                            # Skip if not on main thread
                            return None
                        return original_tcl_call(*args, **kwargs)
                    except Exception as e:
                        print(f"Error in Tcl call: {e}")
                        return None
                
                # Apply the patch if possible
                try:
                    _tkinter.tcl_call = safe_tcl_call
                    print("Applied thread-safety patch to _tkinter.tcl_call")
                except (AttributeError, TypeError) as e:
                    print(f"Could not patch _tkinter.tcl_call: {e}")
        except Exception as e:
            print(f"Error attempting to patch _tkinter: {e}")
        
        # Safety for after method
        try:
            import tkinter
            original_after = tkinter.Misc.after
            
            @functools.wraps(original_after)
            def safe_after(self, ms, func=None, *args):
                if func is None or not callable(func):
                    # Handle delay-only usage or non-callable func
                    return original_after(self, ms, func, *args)
                
                # Create a safe wrapper for the callback
                @functools.wraps(func)
                def safe_func_wrapper():
                    try:
                        return func()
                    except Exception as e:
                        print(f"Error in after callback: {e}")
                        return None
                
                # Schedule with the safe wrapper
                return original_after(self, ms, safe_func_wrapper, *args)
            
            # Apply the patch
            tkinter.Misc.after = safe_after
            print("Applied safety wrapper to tkinter.Misc.after")
        except Exception as e:
            print(f"Could not patch tkinter.Misc.after: {e}")
        
        return True
    except Exception as e:
        print(f"Error applying CustomTkinter patches: {e}")
        import traceback
        traceback.print_exc()
        return False

# Apply patches when imported
if __name__ != "__main__":
    apply_customtkinter_patches()
